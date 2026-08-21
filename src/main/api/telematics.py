from dataclasses import dataclass

from fastapi import APIRouter, HTTPException  # type: ignore[import]
from pydantic import BaseModel, Field  # type: ignore[import]

import numpy as np  # type: ignore[import]

from typing import Dict, List, Optional
from ..sockets.connection_manager import manager

# Create an isolated telemetry module router
router = APIRouter(prefix="/telematics", tags=["telematics"])

VEHICLE_TELEMETRY_STREAM: Dict[str, Dict[int, List[float]]] = {}
WINDOW_SIZE = 3

# ------ GEOLOCATION BOUNDRIES (Example: Bree Street Taxi Rank Hub) ----
BREE_RANK_GEOFENCE = {"lat": -26.2012, "lon": 28.0401, "radius_km": 0.15}


class SeatTelemetry(BaseModel):
    vehicle_id: str
    seat_number: int = Field(..., ge=1, le=16)  # Adds validation boundaries
    accel_variance: float 
    accel_magnitude: float
    # Smartphone sensor fusion fields
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    speed_kmh: Optional[float] = None

@dataclass
class Geofence:
    centre_lat: float
    centre_lon: float
    radius_km: float

def is_inside_geofence(lat: Optional[float], lon: Optional[float], geofence: Dict[str, float]) -> bool:
    """ Calculate roughly if the commuter is sitting inside a major taxi rank zone."""
    if lat is None or lon is None:
        return False
    
    # Simplified bounding-box check fro performance
    lat_delta = abs(lat - geofence["lat"])
    lon_delta = abs(lon - geofence["lon"])
    return lat_delta < 0.001 and lon_delta <0.001

    # --- GEOFENCE check for when vehicle is physically within a designated service area (e.g., Bree Street Taxi Rank) ---
    # This is a placeholder for geospatial calculations. In a real-world scenario,
    # from geopy.distance import distance  # type: ignore[import]
    # center = (geofence["lat"], geofence["lon"])
    # point = (lat, lon)
    # return distance(center, point).km <= geofence["radius_km"]

def evaluate_cluster_decoupling(data: SeatTelemetry) -> str:

    # ----- SENSOR FUSION 1: GPS Speed Check -----
    # If the smartphone confirms the vehicle speed is 0, freeze disembarkation logic
    if data.speed_kmh is not None and data.speed_kmh == 0:
        return "STATIONARY_VEHICLE"

    # ----- SENSOR FUSION 2: Geofence Check -----
    # Disable alerts if everyone is loading/unloading at a designated station zone
    if is_inside_geofence(data.latitude, data.longitude, BREE_RANK_GEOFENCE):
        return "STATION_ZONE_FREEZE"


    if data.vehicle_id not in VEHICLE_TELEMETRY_STREAM:
        VEHICLE_TELEMETRY_STREAM[data.vehicle_id] = {}
    if data.seat_number not in VEHICLE_TELEMETRY_STREAM[data.vehicle_id]:
        VEHICLE_TELEMETRY_STREAM[data.vehicle_id][data.seat_number] = []

    VEHICLE_TELEMETRY_STREAM[data.vehicle_id][data.seat_number].append(data.accel_variance)
    if len(VEHICLE_TELEMETRY_STREAM[data.vehicle_id][data.seat_number]) > WINDOW_SIZE:
        VEHICLE_TELEMETRY_STREAM[data.vehicle_id][data.seat_number].pop(0)

    active_seat_variances = [h[-1] for h in VEHICLE_TELEMETRY_STREAM[data.vehicle_id].values() if h]
    if len(active_seat_variances) < 2:
        return "STILL_EMBARKING"

    cluster_median = float(np.median(active_seat_variances))
    if cluster_median < 0.15:
        return "STATIONARY_VEHICLE"

    seat_historical_avg = sum(VEHICLE_TELEMETRY_STREAM[data.vehicle_id][data.seat_number]) / len(VEHICLE_TELEMETRY_STREAM[data.vehicle_id][data.seat_number])

    if seat_historical_avg < 0.20 and cluster_median > 1.2:
        return "DISEMBARKED"
    
    return "STILL_EMBARKING"

@router.post("/seat-update")
async def receive_seat_telematics(data: SeatTelemetry):
    evaluation = evaluate_cluster_decoupling(data)
    
    if evaluation == "DISEMBARKED":
        await manager.broadcast_seat_update(
            vehicle_id=data.vehicle_id,
            seat_number=data.seat_number,
            status="VACANT"
        )
        return {"status": "success", "action": "trigger_fare_close"}
    return {"status": "success", "state": evaluation}