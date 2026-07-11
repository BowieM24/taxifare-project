from __future__ import annotations

from typing import Dict, Any


class PaymentService:
    """Handles payment flow placeholders used by the USSD and telematics demos."""

    def __init__(self) -> None:
        self._payments: Dict[str, Dict[str, Any]] = {}

    def create_payment(self, vehicle_id: str, seat_number: int, method: str) -> Dict[str, Any]:
        payment = {
            "vehicle_id": vehicle_id,
            "seat_number": seat_number,
            "method": method,
            "status": "pending",
        }
        self._payments[f"{vehicle_id}:{seat_number}"] = payment
        return payment
