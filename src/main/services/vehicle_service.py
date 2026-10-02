from __future__ import annotations

from typing import Dict, Any


class VehicleService:
    """Simplified service layer for vehicle and fleet operations."""

    def __init__(self) -> None:
        self._vehicles: Dict[str, Dict[str, Any]] = {}

    def register_vehicle(self, vehicle_id: str, seat_count: int) -> Dict[str, Any]:
        self._vehicles[vehicle_id] = {
            "vehicle_id": vehicle_id,
            "seat_count": seat_count,
            "status": "registered",
        }
        return self._vehicles[vehicle_id]
