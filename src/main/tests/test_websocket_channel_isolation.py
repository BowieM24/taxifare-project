import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.main.app import app

@pytest.fixture
def sync_client():
    """Provides a TestClient for handling multiple simultaneous WebSockets."""
    with TestClient(app) as client:
        yield client


def test_websocket_messages_are_isolated_by_vehicle_id(sync_client):
    """
    Channel Isolated Test:
    1. Driver A connects to /ws/fleet/TAXI-GP-001.
    2. Driver B connects to /ws/fleet/TAXI-JHB-002.
    3. Webhook fires payment for TAXI-GP-001 (Seat 4).
    4. Assert Driver A receives the frame.
    5. Assert Driver B receives No frame (prevents cross-vehicle data leaks).
    """
    target_vehicle = "TAXI-GP-001"
    other_vehicle = "TAXI-JHB-002"

    with patch("src.main.api.notification.is_transaction_processed", new_callable=AsyncMock) as mock_idempotency:
        mock_idempotency.return_value = False   #Mark transaction as new

        # 1. Open Websocket streams for two separate taxis
        with sync_client.websocket_connect(f"/ws/fleet/{target_vehicle}") as ws_target:
            with sync_client.websocket_connect(f"/ws/fleet/{other_vehicle}") as ws_other:


                # 2. Trigger webhook for TAXI-GP-001 ONLY
                webhook_payload = {
                    "transaction_id": "TXN-ISOLATION-001",
                    "vehicle_id": target_vehicle,
                    "external_reference": "2",
                    "status": "SUCCESS",
                    "amount": 22.50,
                    "provider": "MTN_MOMO"
                }

                response = sync_client.post("/webhooks/payments", json=webhook_payload)
                assert response.status_code == 200

                # 3. Target vehicle receives the frame
                ws_target_data = ws_target.receive_json()
                assert ws_target_data["vehicle_id"] == target_vehicle
                assert ws_target_data["seat_id"] == 2
                assert ws_target_data["seat_color"] == "GREEN"

                # 4. Other vehicle receives no message (times out gracefully)
                with pytest.raises(Exception):
                    # Setting a  tiny timeout ensures we don't block waiting for a message that shouldn't arrive
                    ws_other.receive_json(timeout=0.2)



