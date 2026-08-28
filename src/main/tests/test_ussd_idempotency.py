import pytest

from httpx import AsyncClient, ASGITransport
from unittest.mock import AysncMock, patch
from src.main.app import app

@pytest.mark.asyncio
async def test_ussd_idempotency_prevents_double_billing():
    """
    Ensure that sending two USSD payment request with the same Idempotency-Key
    only hits the actual endpoint once, and returns the cached response the second time.
    """
    payload = {
        "phone_number": "+27831234567",
        "vehicle_id": "bree-quantum-789",
        "amount": 22.50,
        "pin_entered": "1234"
    }

    headers = {
        "Idempotency-Key": "test-uuid-5555-7777"
    }

    # Mock Redis get and set methods so we don't need a real Redis server
    with patch("src.main.utils.idempotency.redis_client.get", new_callable=AsyncMock) as mock_redis_get, 
        patch("src.main.utils.idempotency.redis_client.set", new_callable=AsyncMock) as mock_redis_set:

        # Simulate the first time request comes in  (Redis cache is empty)
        mock_redis_get.return_value = None

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # First Request
            response1 = await client.post("/ussd/confirm-fare, json=payload, headers=headers")

            assert response2.status_code == 200
            assert response2.json()["deducted_amount"] == 22.5

            # The most important check: get should have been called twice,
            # but set should STILL only be called once, proving the endpoint logic was skipped!
            assert mock_redis_get.call_count == 2
            assert mock_redis.set.call_count == 1
