import httpx

from aiobreaker import CircuitBreaker
from datetime import timedelta

# Circuit trips after 5 consecutive failures, testing recovery after 60 seconds
gateway_breaker = CircuitBreaker(fail_max=5, timeout_duration=timedelta(seconds=60))

@gateway_breaker
async def charge_commuter_account_via_electrum(amount: float, phone_number: str, vehicle_id: str):
    """
    Initiates a charge via the Electrum Regulated Payments Partner API.
    """
    async with httpx.AsyncClient() as client:
        # Electrum API payload structure
        payload = {
            "amount": amount,
            "proxy_id": phone_number,
            "reference": vehicle_id
        }

            # This will raise an exception if Electrum times out, triggering thr breaker
        response = await client.post(
            "https://api.electrum.co.za/v1/transactions/outbound", 
            json=payload,
            timeout=5.0
        )
        response.raise_for_status()
        return response.json()