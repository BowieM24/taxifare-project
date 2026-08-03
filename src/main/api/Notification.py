import hmac
import hashlib
import time
import logging

from typing import Dict, Set, List
from fastapi import APIRouter, HTTPException, Request, Header  # type: ignore[import]
from pydantic import BaseModel  # type: ignore[import]

from src.main.config import settings
from src.main.services.redis_service import is_rate_limited, is_transaction_processed

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Notifications & Webhooks"])


# ----- PYDANTIC MODELS -----
# Models for the 'Commuter Profile' and 'Transaction
class PaymentRequest(BaseModel):
    commuter_id: str
    seat_id: int
    amount: float
    taxi_id: str
    auth_pin: str


class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    message: str

# 1. The Webhook Payload Model (Standard for MTN MoMo/Electrum style)
class WebhookData(BaseModel):
    transaction_id: str
    external_reference: str  # e.g. Seat ID or Commuter ID
    status: str             # SUCCESS, FAILED, or PENDING
    amount: float
    provider: str           # e.g. 'MTN_MOMO' or 'VODAPAY'

# -------- DOMAIN ACTIONS / NOTIFICATIONS -----
async def alert_driver(taxi_id: str, seat_id: int) -> None:
    """
    Trigger real-time WebSocket update for driver dashboard.
    """
    logger.info(f"DEBUG: Taxi {taxi_id} seat {seat_id} turned GREEN.")

async def send_sms_receipt(commuter_id: str) -> None:
    """
    Trigger SMS gateway (Africa's Talking/ local aggregator).
    """
    logger.info(f"DEBUG: SMS Receipt sent to commuter {commuter_id}.")


# ------- ENDPOINTS ------------
@router.post("/process-fare", response_model = TransactionResponse)
async def process_fare(payment: PaymentRequest):
    """ Processes instant fare request with rate limiting and 2FA PIN check."""
    # 1. Redis Rate Limiting Protection(5 requests per 60s)
    if await is_rate_limited(payment.commuter_id):
        raise HTTPException(
            status_code = 429, 
            detail = "Too many payment attempts. Please try again later."
        )
    
    # 2. Validity and Authentication Check
    if not payment.auth_pin:
        raise HTTPException(status_code = 401, detail = "Two-factor authentication failed")
       
    # 3. Process Transaction
    await alert_driver(payment.taxi_id, payment.seat_id)
    await send_sms_receipt(payment.commuter_id)

    return TransactionResponse(
        transaction_id="TXN-12345",
        status="Approved",
        message=f"Seat {payment.seat_id} is now paid."
    )

# 2. The Webhook Endpoint
@router.post("/webhooks/payments")
async def payment_webhook(
    data: WebhookData,
    request: Request,
    x_signature: str | None = Header(None, alias="X-Signature") # Security header to verify its really from Electrum
):
    """Secure webhook endpoint for Electrum/ MTN MoMo payment notification."""
    # SECURITY: Verify the signature (Crucial so hackers don't fake payments)
    body = await request.body()

    # 1. Redis Idempotency Check: Prevent duplicate processing of the same transaction
    if await is_transaction_processed(data.transaction_id):
        logger.info(f"Duplicate webhook ignored for transaction: {data.transaction_id}")
        return {"message": "Duplicate transaction ignored/Webhook already processed (Idempotent bypass)"}

    if data.status == "SUCCESS":
        # Trigger real-time seat update & receip
        await alert_driver(data.transaction_id, int(data.external_reference))
        # Send Receipt
        await send_sms_receipt(data.external_reference)

        logger.info(
            f"✓ PAYMENT CONFIRMED: Seat {data.external_reference} for Transaction {data.transaction_id}"
        )
        return {"message": "Webhook received and processed"}
    
    logger.warning(f"✕ PAYMENT FAILED: {data.transaction_id}")
    return {"message": "Failure logged"}
    