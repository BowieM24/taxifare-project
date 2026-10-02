import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest                                   # type: ignore[import]
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient       # type: ignore[import]
from src.main.app import app


@pytest.fixture
def sync_client():
    """Provides a TestClient capable of maintaining active WebSocket connections."""
    with TestClient(app) as client:
        yield client


def test_websocket_end_to_end_payment_broadcast(sync_client):
    """
    End-to-End Test Flow:
    1. Driver tablet opens WebSocket connection to /ws/fleet/TAXI-GP-001.
    2. Payment Gateway posts a webhook to /webhooks/payments.
    3. Assert WebSocket receives the real-time 'PAYMENT_RECEIVED' JSON frame turning Seat 4 GREEN.
    """
    vehicle_id = "TXN-12345"
    target_seat = 4

    # Patch Redis functions so the test doesn't require a live Redis instance running
    with patch("src.main.api.notification.is_transaction_processed", new_callable=AsyncMock) as mock_idempotency:
        mock_idempotency.return_value = False  # Mark transaction as new

        # Step 1: Open WebSocket connection for the driver tablet
        with sync_client.websocket_connect(f"/ws/fleet/{vehicle_id}") as websocket:
            # Step 2: Simulate incoming payment webhook POST request from Electrum/MTN MoMo
            webhook_payload = {
                "transaction_id": "TXN-12345",
                "vehicle_id": vehicle_id,
                "external_reference": str(target_seat),
                "status": "SUCCESS",
                "amount": 22.50,
                "provider": "MTN_MOMO"
            }
            response = sync_client.post("/webhooks/payments", json=webhook_payload)
            assert response.status_code == 200
            assert response.json() == {"message": "Payment processed successfully."}

            # Step 3: Receive the broadcasted WebSocket message
            ws_message = websocket.receive_json()
            assert ws_message["event"] == "PAYMENT_RECEIVED"
            assert ws_message["vehicle_id"] == vehicle_id
            assert ws_message["seat_id"] == target_seat
            assert ws_message["status"] == "PAID"
            assert ws_message["seat_color"] == "GREEN"
            assert ws_message["amount"] == 22.50
            assert ws_message["transaction_id"] == "TXN-12345"