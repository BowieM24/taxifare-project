import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_telematics_sensor_fusion_payload(client):
    """
    Test sensor telemetru packet processing without needing a live server.
    """
    payload = {
        "vehicle_id": "bree-quantum-xyz-789",
        "seat_number": 1,
        "accel_variance": 0.02,
        "accel_magnitude": 9.81
    }

    # Patch the manager broadcast call inside telematics route
    with patch("src.main.api.telematics.manager.broadcast_seat_update", new_callable=AsyncMock) as mock_broadcast:
        response = await client.post("/telematics/seat-update", json=payload)

        assert response.status_code == 200
        assert response.json()["status"] == "success"

@pytest.mark.asynico
async def test_telematics_out_of_bounds_seat_rejection(client):
    """
    Ensure invalid seat number (e.g. seat 99) return HHTP 442 payload errors.
    """
    invalid_payload = {
        "vehicle_id": "bree-quantum-xyz-789",
        "seat_number": 99,
        "accel_variance": 0.05,
        "accel_magnitude": 9.81
    }

    response = await client.post("/telematics/seat-update", json=invalid_payload)
    assert response.status_code == 422