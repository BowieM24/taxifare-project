import logging
import json
import asyncio

from fastapi import WebSocket  # type: ignore[import]
from typing import Dict, List
from src.main.database_src.redis import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Map vehicle_id -> list of active WebSocket connections for that vehicle
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.pubsub = redis_client.pubsub()
        self.listener_task = None

    async def start_redis_listener(self):
        """ Background task that listens for meaasge from OTHER worker."""
        await self.pubsub.subscribe("taxi_seat_updates")
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                payload = json.loads(message["data"])
                target_vehicle = payload["vehicle_id"]

                # If this specific worker has the WebSocket for the vehicle, send it!
                if target_vehicle in self.active_connections:
                    for connection in self.active_connections[target_vehicle]:
                        try:
                            await connection.send_json(payload)
                        except Exception as e:
                            logger.error(f"WebSocket send failed: {e}")
    
    async def connect(self, vehicle_id: str, websocket: WebSocket):
        """Accepts connection and registers it under the specific vehicle ID."""
        await websocket.accept()
        if vehicle_id not in self.active_connections:
            self.active_connections[vehicle_id] = []
        self.active_connections[vehicle_id].append(websocket)
        # Start the Redis Listener only once when 1st connection is made
        if self.listener_task is None:
            self.listener_task = asyncio.create_task(self.start_redis_listener()) 
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
        """ Instead of sending directly, Publish to Redis so all workkers see it."""
        # if vehicle_id not in self.active_connections:
        #     logger.warning(f"No active WebSocket clients connected for vehicle {vehicle_id}. Skipping broadcast.")
        #     return
         
        payload = {
                "event": "PAYMENT_RECEIVED",
                "vehicle_id": vehicle_id,
                "seat_id": seat_id,
                "status": status, # e.g. "PAID" (Turns Green) or "VACANT" (Turns Gray)
                "seat_color": "GREEN" if status == "PAID" else "GRAY",
                "amount": float(amount),
                "transaction_id": tx_id,
        }
        # Publish the event to the Redis channel
        await redis_client.publish("taxi_seat_updates", json.dumps(payload))

# Global singleton instance used across the app
manager = ConnectionManager()

