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
    await manager.connect(mock_websocket, vehicle_id)
    assert vehicle_id in manager.active_connections
    assert mock_websocket in manager.active_connections[vehicle_id]

    # Test disconnection
    manager.disconnect(mock_websocket, vehicle_id)
    assert mock_websocket not in manager.active_connections[vehicle_id]


@pytest.mark.asyncio
async def test_websocket_channel_isolation():
    """
    Ensure seat broadcasts only route to websockets for the matching vehicle_id.
    """
    manager = ConnectionManager()

    ws_vehicle_a = AsyncMock()
    ws_vehicle_b = AsyncMock()

    # Register two distinct taxi's
    await manager.connect(ws_vehicle_a, "bree-quantum-xyz-789")
    await manager.connect(ws_vehicle_b, "randburg-quantum-abc-123")

    # Broadcast to Taxi A
    await manager.broadcast_seat_update(
        vehicle_id="bree-quantum-xyz-789",
        seat_number=4,
        status="PAID"
    )

    # Taxi A receives the JSON payload
    ws_vehicle_a.send_json.assert_called_once_with({
        "seat_number": 4,
        "status": "PAID"
    })

    # Taxi B receives nothing
    ws_vehicle_b.send_json.assert_not_called()