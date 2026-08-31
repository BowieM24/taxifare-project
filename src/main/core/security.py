import secrets
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks       # type: ignore[import]
from pydantic import BaseModel          # type: ignore[import]

from ..database_src.redis import redis_client
from src.main.api.notification import send_sms_receipt


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Commuter Security"])

OTP_EXPIRY_SECONDS = 180     # OTP valid for 3 minutes

class OTPGenerateRequest(BaseModel):
    phone_number: str

class OTPVerifyRequest(BaseModel):
    phone_number: str
    otp: str
    transaction_id: str


async def generate_otp() -> str:
    """Generate a secure 4-digit OTP."""
    return str(secrets.randbelow(10000)).zfill(4)

@router.post("/generate-otp")
async def  request_payment_otp(payload: OTPGenerateRequest, background_tasks: BackgroundTasks):
    """
    Generates a 4-digit PIN and stores it in Redis with a 3-minute expiry.
    Dispatches an SMS to the commuter.
    """
    otp = await generate_otp()
    redis_key = f"otp:{payload.phone_number}"

    # Store OTP in Redis with an expiration time
    await redis_client.set(redis_key, otp, ex=OTP_EXPIRY_SECONDS)

    # Simulate sending SMS in the background
    sms_message = f"TaxiFare™: Your payment authorization PIN is {otp}. Do not share this code. Valid for 3 minutes."
    background_tasks.add_task(send_sms_receipt, payload.phone_number, sms_message)   # Update SMS function to accept custom text if needed

    logger.info(f"OTP generated for {payload.phone_number}")
    return {"message": "OTP sent to your registered mobile number."}


@router.post("/verify-otp")
async def verify_payment_otp(payload: OTPVerifyRequest):
    """
    Verifies the commuter's OTP against Redis.
    If valid, it allows the payment pipeline to processed.
    """
    redis_key = f"otp:{payload.phone_number}"
    stored_otp = await redis_client.get(redis_key)

    if not stored_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP entered.")

    if stored_otp != payload.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP entered.")

    # Delete the OTP immediately after successful use to prevent replay attacks
    await redis_client.delete(redis_key)

    logger.info(f"OTP verified successfully for {payload.phone_number} on tx {payload.transaction_id}")
    return {
        "status": "authenticated",
        "message": "Payment authorized successfully."
    }