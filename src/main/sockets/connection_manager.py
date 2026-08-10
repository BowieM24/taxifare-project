import logging
from fastapi import WebSocket  # type: ignore[import]
from typing import Dict, List


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Map vehicle_id -> list of active WebSocket connections for that vehicle
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, vehicle_id: str, websocket: WebSocket):
        """Accepts connection and registers it under the specific vehicle ID."""
        await websocket.accept()
        if vehicle_id not in self.active_connections:
            self.active_connections[vehicle_id] = []
        self.active_connections[vehicle_id].append(websocket)
        logger.info(f"🖥️ Driver/Display linked to streaming pipe for vehicle: {vehicle_id}")


    def disconnect(self, vehicle_id: str, websocket: WebSocket):
        """Removes closed connection from active registry."""
        if vehicle_id in self.active_connections:
            if websocket in self.active_connections[vehicle_id]:
                self.active_connections[vehicle_id].remove(websocket)
            if not self.active_connections[vehicle_id]:  # Clean up if no more connections
                del self.active_connections[vehicle_id]
        logger.info(f"🔌 Display disconnected from vehicle stream: {vehicle_id}")

    async def broadcast_seat_update(self, vehicle_id: str, seat_id: int, amount: float, tx_id: str, status: str):
        """ Broadcast a real_time message to all displays registered to this taxi."""
        if vehicle_id not in self.active_connections:
            logger.warning(f"No active WebSocket clients connected for vehicle {vehicle_id}. Skipping broadcast.")
            return
         
        payload = {
                "event": "PAYMENT_RECEIVED",
                "vehicle_id": vehicle_id,
                "seat_id": seat_id,
                "status": "PAID", # e.g. "PAID" (Turns Green) or "VACANT" (Turns Gray)
                "seat_color": "GREEN",
                "amount": amount,
                "transaction_id": tx_id,
        }
        # Send JSON payload to all HUD devices bound to this taxi
        for connection in self.active_connections[vehicle_id]:
                try:
                    await connection.send_json(payload)
                except Exception as e:
                    logger.error(f"Error broadcasting payment update for seat {seat_id} to vehicle {vehicle_id}: {e}")
# Global singleton instance used across the app
manager = ConnectionManager()

