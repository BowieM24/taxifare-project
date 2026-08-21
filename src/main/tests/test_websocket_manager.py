import pytest   # type: ignore[import]

from unittest.mock import AsyncMock, MagicMock
from src.main.sockets.connection_manager import ConnectionManager   # type: ignore[import]

@pytest.mark.asyncio
async def test_connection_manager_connect_and_disconnect():
    """
    Verify connection are mapped to channels and cleaned up upon disconnect.
    """
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    vehicle_id = "bree-quantum-xyz-789"
    
    # Test connection
    await manager.connect(vehicle_id, mock_websocket)
    assert vehicle_id in manager.active_connections
    assert mock_websocket in manager.active_connections[vehicle_id]

    # Test disconnection
    manager.disconnect(vehicle_id, mock_websocket)
    assert vehicle_id not in manager.active_connections


@pytest.mark.asyncio
async def test_websocket_channel_isolation():
    """
    Ensure seat broadcasts only route to websockets for the matching vehicle_id.
    """
    manager = ConnectionManager()

    ws_vehicle_a = AsyncMock()
    ws_vehicle_b = AsyncMock()

    # Register two distinct taxi's
    await manager.connect("bree-quantum-xyz-789", ws_vehicle_a)
    await manager.connect("randburg-quantum-abc-123", ws_vehicle_b)

    # Broadcast to Taxi A
    await manager.broadcast_seat_update(
        vehicle_id="bree-quantum-xyz-789",
        seat_id=4,
        amount=150.00,
        tx_id="txn-001",
        status="PAID",
    )

    # Taxi A receives the JSON payload
    ws_vehicle_a.send_json.assert_called_once_with({
        "event": "PAYMENT_RECEIVED",
        "vehicle_id": "bree-quantum-xyz-789",
        "seat_id": 4,
        "status": "PAID",
        "seat_color": "GREEN",
        "amount": 150.00,
        "transaction_id": "txn-001"
    })

    # Taxi B receives nothing
    ws_vehicle_b.send_json.assert_not_called()