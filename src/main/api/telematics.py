from fastapi import APIRouter  # type: ignore[import]
from pydantic import BaseModel  # type: ignore[import]

import numpy as np  # type: ignore[import]

from typing import Dict, List
from ..sockets.connection_manager import manager

# Create an isolated telemetry module router
router = APIRouter(prefix="/telematics", tags=["telematics"])

VEHICLE_TELEMETRY_STREAM: Dict[str, Dict[int, List[float]]] = {}
WINDOW_SIZE = 3


class SeatTelemetry(BaseModel):
    vehicle_id: str
    seat_number: int
    accel_variance: float 
    accel_magnitude: float

def evaluate_cluster_decoupling(vehicle_id: str, new_seat: int, new_variance: float) -> str:
    if vehicle_id not in VEHICLE_TELEMETRY_STREAM:
        VEHICLE_TELEMETRY_STREAM[vehicle_id] = {}
    if new_seat not in VEHICLE_TELEMETRY_STREAM[vehicle_id]:
        VEHICLE_TELEMETRY_STREAM[vehicle_id][new_seat] = []

    VEHICLE_TELEMETRY_STREAM[vehicle_id][new_seat].append(new_variance)
    if len(VEHICLE_TELEMETRY_STREAM[vehicle_id][new_seat]) > WINDOW_SIZE:
        VEHICLE_TELEMETRY_STREAM[vehicle_id][new_seat].pop(0)

    active_seat_variances = [h[-1] for h in VEHICLE_TELEMETRY_STREAM[vehicle_id].values() if h]
    if len(active_seat_variances) < 2:
        return "STILL_EMBARKING"

    cluster_median = float(np.median(active_seat_variances))
    if cluster_median < 0.15:
        return "STATIONARY_VEHICLE"

    seat_historical_avg = sum(VEHICLE_TELEMETRY_STREAM[vehicle_id][new_seat]) / len(VEHICLE_TELEMETRY_STREAM[vehicle_id][new_seat])

    if seat_historical_avg < 0.20 and cluster_median > 1.2:
        return "DISEMBARKED"
    
    return "STILL_EMBARKING"

@router.post("/seat-update")
async def receive_seat_telematics(data: SeatTelemetry):
    evaluation = evaluate_cluster_decoupling(data.vehicle_id, data.seat_number, data.accel_variance)
    if evaluation == "DISEMBARKED":
        await manager.broadcast_seat_update(
            vehicle_id=data.vehicle_id,
            seat_number=data.seat_number,
            status="VACANT"
        )
        return {"status": "processed", "action": "trigger_fare_close"}
    return {"status": "processed", "state": evaluation}