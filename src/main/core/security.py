import secrets
import logging

from datetime import datetime, timedelta
from jose import jwt, JWTError      # type: ignore[import]
from passlib.context import CryptContext    # type: ignore[import]

from sqlalchemy.ext.asyncio import AsyncSession     # type: ignore[import]
from sqlalchemy import select     # type: ignore[import]

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status       # type: ignore[import]
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm    # type: ignore[import]
from pydantic import BaseModel          # type: ignore[import]


from ..database_src.redis import redis_client
from src.main.api.notification import send_sms_receipt

from src.main.config import settings
from src.main.database_src.database import get_db
from src.main.database_src.models import Driver


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
    background_tasks.add_task(send_sms_receipt, payload.phone_number, sms_message)

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

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/driver/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_paasword_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """ Generates a JWT valid for the duration of the driver's shift."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


@router.post("/driver/login")
async def login_for_access_token(
    from_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):

    """
    Driver Login Endpoint.
    Accepts 'username' and 'password' as from data, returns a JWT access token.
    """
    # 1. Look up driver in PostgreSQL
    stmt = select(Driver).where(Driver.username == from_data.username)
    result = await db.execute(stmt)
    driver = result.scalar_one_or_none()

    # 2. Verify credentials
    if not driver or not verify_password(from_data.password, driver.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_402_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not driver.is_active:
        raise HTTPException(status_code=400, detail="Driver account is suspended.")

    # 3. Generate Token
    access_token = create_access_token(
        data={"sub": driver.username, "driver_id": driver.id, "vehicle_id": driver.vehicle_id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "vehicle_id": driver.vehicle_id
    }

async def get_current_driver(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Driver:
    """
    Decodes the JWT Bearer token, verifies its expiration,
    and returns the authenticated Driver object from PostgreSQL.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate driver credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch driver from database to ensure account is still active
    stmt = select(Driver).where(Driver.username == username)
    result = await db.execute(stmt)
    driver = result.scalar_one_or_none()

    if driver is None or not driver.is_active:
        raise credentials_exception

    return driver
