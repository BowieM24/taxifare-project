import httpx
import uuid
import os

from fastapi import HTTPException

async def validate_vehicle_registration(registration_number: str, vin: str):
    """
    Validate a vehicle's registration and roadworthy status using VerifyNow

    """

    url = "https://www.verifynow.co.za/api/external/vehicle-check"

    headers = {
        "x-api-key": os.getenv("VERIFYNOW_API_KEY"),
        "Content-Type": "application/json",
        "Idempotency-Key": str(uuid.uuid4())
    }

    payload = {
        "registrationNumber": registration_number,
        "vin": vin,
        "mode": "sandbox"   # Keep in sandbox mode until production launch        
    }

    async with httpx.AsyncClient() as client:
        reponse = await client.post(url, json=payload, headers=headers, timeout=10.0)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Vehicle compliance validation failed via VerifyNow."
            )

            return response.json()
