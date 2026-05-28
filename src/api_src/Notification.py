from fastapi import FastAPI, HTTPException, Request, Header  # type: ignore[import]
from pydantic import BaseModel
import hmac
import hashlib
import time

# Use previous app setup
app = FastAPI(title="TaxiFare API")

# ---- IN-MEMORY CACHES (Replace with Redis in Production) ----
PROCESSED_TRANSACTIONS = set()  # For idempotency and duplicate prevention
RATE_LIMIT_TRACKER = {}  # For rate limiting (commuter_id: [timestamps])


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
    external_reference: str # Seat ID or Commuter ID
    status: str             # SUCCESS, FAILED, or PENDING
    amount: float
    provider: str           # e.g. 'MTN_MOMO' or 'VODAPAY'

# ---- UTILITIES --- Helper for security (Electrum/MTN usually use HMAC-SHA256)
def verify_signature(payload: bytes, signature: str):
    SECRET = b"your_electrum_webhook_secret"  #Keep this secure in production
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

# Core API functions (Placeholders for real logic)
def alert_driver(taxi_id: str, seat_id: int):
    print(f"DEBUG: Taxi {taxi_id} seat {seat_id} turned GREEN.")

def send_sms_receipt(communter_id: str):
    print(f"DEBUG: SMS Receipt sent to commuetr {communter_id}.")

# Endpoints
@app.post("/process-fare", response_model = TransactionResponse)
async def process_fare(payment: PaymentRequest):
    # 1. Rate Limiting Protection
    if is_rate_limited(payment.commuter_id):
        raise HTTPException(status_code = 429, detail = "Too many payment attempts. Please try again later.")
    
    # 2. Validity and Authentication 
    if not payment.auth_pin:
        raise HTTPException(status_code = 401, detail = "Two-factor authentication failed")
       
    # 3. Simulate Request transaction to Merchant/Bank (Mocked logic)
    transaction_approved = True

    if transaction_approved:
        # 4. Alert Taxi Driver
        alert_driver(payment.taxi_id, payment.seat_id)

        # 5. Digital Receipt via SMS
        send_sms_receipt(payment.commuter_id)

        return {
            "transaction_id": "TXN-12345",
            "status": "Approved",
            "message": f"Seat {payment.seat_id} is now paid."
        }
    else:
        return {"transaction_id": "TXN-0000", "status": "Declined", "message": "Insufficient funds"}

# 2. The Webhook Endpoint
@app.post("/webhooks/payments")
async def payment_webhook(
    data: WebhookData,
    request: Request,
    x_signature: str = Header(None) # Security header to verify its really from Electrum
):
    # SECURITY: Verify the signature (Crucial so hackers don't fake payments)
    body = await request.body()
    # verify_signature(awiat request.body(), x_signature)

    # 6. Idempotency Check: Prevent duplicate processing of the same transaction
    if data.transaction_id in PROCESSED_TRANSACTIONS:
        return {"message": "Duplicate transaction ignored/Webhook already processed (Idempotent bypass)"}

    if data.status == "SUCCESS":
        # A. Update Database: Mark transaction as 'Paid'
        # update_db_transaction_status(data.tranaction_id, "APPROVED")
        PROCESSED_TRANSACTIONS.add(data.transaction_id)  # Mark as processed for idempotency

        # B. Real-time Action: Trigger the Seat to turn Green
        alert_driver(data.transaction_id, int(data.external_reference))
        # This talks to the Driver's App via WebSockets
        print(f"✓ PAYMENT CONFIRMED: Seat {data.external_reference} for Taxi {data.transaction_id}")

        # C. Send  Receipt
        send_sms_receipt(data.external_reference)

        return {"message": "Webhook received and processed"}
    
    else:
        print(f"✕ PAYMENTY FAILED: {data.transaction_id}")
        return {"message": "Failure logged"}
    

# Helper for security (Electrum/MTN usually use HMAC-SHA256)
# def verify_signature(payload: bytes, signature: str):
#     secret = b"your_electrum_webhook_secret"
#     expected_sig = hmac.new(secret, payload, hashlib.sha256)


# Models for the 'Commuter Profile' and 'Transaction'
class PaymentRequest(BaseModel):
    commuter_id: str
    seat_id: int
    amount: float
    taxi_id: str
    auth_pin: str  # Simulated 2FA/PIN [cite: 2]

class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    message: str

@app.post("/process-fare", response_model=TransactionResponse)
async def process_fare(payment: PaymentRequest):
    # 1. Validity and Authentication [cite: 2]
    # In a real app, you would verify the PIN and Commuter Profile here.
    if not payment.auth_pin:
        raise HTTPException(status_code=401, detail="Two-factor authentication failed")

    # 2. Request transaction to Merchant/Bank [cite: 2]
    # Logic to interface with an Internet Gateway like Stitch or Ozow
    transaction_approved = True  # Mocked logic 

    if transaction_approved:
        # 3. Alert Taxi Driver 
        # This would trigger a WebSocket message to turn the seat 'green'
        alert_driver(payment.taxi_id, payment.seat_id)
        
        # 4. Digital Receipt via SMS 
        send_sms_receipt(payment.commuter_id)

        return {
            "transaction_id": "TXN-12345",
            "status": "Approved",
            "message": f"Seat {payment.seat_id} is now paid."
        }
    else:
        # Handle 'Not Approved' path 
        return {"transaction_id": "TXN-0000", "status": "Declined", "message": "Insufficient funds"}

def alert_driver(taxi_id: str, seat_id: int):
    # Placeholder for WebSocket/Real-time logic
    print(f"DEBUG: Taxi {taxi_id} seat {seat_id} turned GREEN.")

def send_sms_receipt(commuter_id: str):
    # Placeholder for Twilio/SMS Gateway logic 
    print(f"DEBUG: SMS Receipt sent to commuter {commuter_id}.")
    