from fastapi import WebSocket  # type: ignore[import]
from typing import Dict, List


class DriverSocketManager:
    def __init__(self):
        # Map active connections: {vehicle_id: [List of connected driver/passenger tablets]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, vehicle_id: str, websocket: WebSocket):
        await websocket.accept()
        if vehicle_id not in self.active_connections:
            self.active_connections[vehicle_id] = []
        self.active_connections[vehicle_id].append(websocket)
        print(f"🖥️ Driver/Display linked to streaming pipe for vehicle: {vehicle_id}")


    def disconnect(self, vehicle_id: str, websocket: WebSocket):
        if vehicle_id in self.active_connections:
            if websocket in self.active_connections[vehicle_id]:
                self.active_connections[vehicle_id].remove(websocket)
            if not self.active_connections[vehicle_id]:  # Clean up if no more connections
                del self.active_connections[vehicle_id]

        print(f"🔌 Display disconnected from vehicle stream: {vehicle_id}")

    async def broadcast_seat_update(self, vehicle_id: str, seat_number: int, status: str):
         """ Sends a real_time message to all displays registered to this taxi."""
         if vehicle_id in self.active_connections:
            payload = {
                "event": "SEAT_UPDATE",
                "seat_number": seat_number,
                "status": status  # e.g. "PAID" (Turns Green) or "VACANT" (Turns Gray)
            }
            for connection in self.active_connections[vehicle_id]:
                await connection.send_json(payload)
                print(f"📡 Broadcasted seat {seat_number} status change to vehicle {vehicle_id}")

manager = DriverSocketManager()

