import json
from fastapi import APIRouter, Request, HTTPException      # type: ignore[import]
from pydantic import BaseModel              # type: ignore[import]
from aiobreaker import CircuitBreakerError

from src.main.core.electrum_gateway import charge_commuter_account_via_electrum
from ..utils.idempotency import idempotent_transaction   # type: ignore[import]
from src.main.database_src.redis import redis_client
from src.main.utils.rate_limiter import limiter

router = APIRouter(prefix="/ussd", tags=["ussd"])

class USSDPaymentPayload(BaseModel):
    phone_number: str
    vehicle_id: str
    amount: float
    pin_entered: str

@router.post("/confirm-fare")
@limiter.limit("5/minute")
@idempotent_transaction(expire_seconds=86400)
async def confirm_ussd_fare(request: Request, payload: USSDPaymentPayload):
    try:
        # Attempt to charge the account live
        result = await charge_commuter_account_via_electrum(
            amount=payload.amount,
            phone_number=payload.phone_number,
            vehicle_id=payload.vehicle_id
        )
        return {
        "status": "success",
        "message": "fare deducted successfully",
        "data": result
        }

    except (CircuitBreakerError, Exception) as e:
        # The gateway is down! Fallback to the Offline Tolerance Queue
        queue_payload = payload.model_dump_json()

        # Push raw transaction data to a Redis List
        await redis_client.lpush("offline_ussd_transactions", queue_payload)

        # Return success to the commuter so they can board the taxi
        return {
            "status": "queued",
            "message": "Network unstable. Fare queued for processing."
        }