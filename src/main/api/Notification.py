import hmac
import hashlib
import time
import logging

from typing import Dict, Set, List
from fastapi import APIRouter, HTTPException, Request, Header  # type: ignore[import]
from pydantic import BaseModel  # type: ignore[import]

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Notifications & Webhooks"])

# Configuration (Use environment variables in production)
ELECTRUM_WEBHOOK_SECRET = b"our_electrum_webhook_secret"

# ---- IN-MEMORY CACHES (Replace with Redis in Production) ----
PROCESSED_TRANSACTIONS: Set[str] = set()  # For idempotency and duplicate prevention
RATE_LIMIT_TRACKER: Dict[str, List[float]] = {}  # For rate limiting (commuter_id: [timestamps])

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
    external_reference: str # e.g. Seat ID or Commuter ID
    status: str             # SUCCESS, FAILED, or PENDING
    amount: float
    provider: str           # e.g. 'MTN_MOMO' or 'VODAPAY'

# ---- UTILITIES --- Helper for security (Electrum/MTN usually use HMAC-SHA256)
def verify_signature(payload: bytes, signature: str | None) -> None:
    SECRET = ELECTRUM_WEBHOOK_SECRET  # Keep this secure in production
    if not signature:
        raise HTTPException(status_code=401, detail = "Missing security signature")
    
    expected_sig = hmac.new(SECRET, payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        raise HTTPException(status_code = 401, detail = "Invalid signature authentication")

def is_rate_limited(commuter_id: str, limit: int = 5, window: int = 60) -> bool:
    """Limits a commuter to 5 payments requests per 60 seconds."""
    current_time = time.time()

    if commuter_id not in RATE_LIMIT_TRACKER:
        RATE_LIMIT_TRACKER[commuter_id] = []

    # Filter out timestamps older than our window
    RATE_LIMIT_TRACKER[commuter_id] = [t for t in RATE_LIMIT_TRACKER[commuter_id] if current_time - t < window]
    
    if len(RATE_LIMIT_TRACKER[commuter_id]) >= limit:
        return True  # Rate limit exceeded
    
    RATE_LIMIT_TRACKER[commuter_id].append(current_time)
    return False

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
    # 1. Rate Limiting Protection(Check)
    if is_rate_limited(payment.commuter_id):
        raise HTTPException(
            status_code = 429, 
            detail = "Too many payment attempts. Please try again later."
        )
    
    # 2. Validity and Authentication Check
    if not payment.auth_pin:
        raise HTTPException(status_code = 401, detail = "Two-factor authentication failed")
       
    # 3. Simulate Request transaction to Merchant/Bank (Mocked logic)
    transaction_approved = True

    if transaction_approved:
        # 4. Alert Taxi Driver
        await alert_driver(payment.taxi_id, payment.seat_id)

        # 5. Digital Receipt via SMS
        await send_sms_receipt(payment.commuter_id)

        return TransactionResponse(
            transaction_id="TXN-12345",
            status="Approved",
            message=f"Seat {payment.seat_id} is now paid."
        )

    return TransactionResponse(
        transaction_id="TXN-0000",
        status="Declined",
        message="Insufficient funds"
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
    verify_signature(body, x_signature)

    # 6. Idempotency Check: Prevent duplicate processing of the same transaction
    if data.transaction_id in PROCESSED_TRANSACTIONS:
        return {"message": "Duplicate transaction ignored/Webhook already processed (Idempotent bypass)"}

    if data.status == "SUCCESS":
        # A. Update Database: Mark transaction as 'Paid'
        PROCESSED_TRANSACTIONS.add(data.transaction_id)  # Mark as processed for idempotency

        # B. Real-time Action: Trigger the Seat to turn Green
        # external_reference is expected to be a seat id in this simplified model
        await alert_driver(data.transaction_id, int(data.external_reference))
        # C. Send Receipt
        await send_sms_receipt(data.external_reference)

        logger.info(
            f"✓ PAYMENT CONFIRMED: Seat {data.external_reference} for Transaction {data.transaction_id}"
        )
        return {"message": "Webhook received and processed"}
    
    logger.warning(f"✕ PAYMENT FAILED: {data.transaction_id}")
    return {"message": "Failure logged"}
    

# End of file
    