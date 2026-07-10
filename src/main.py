from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status, HTTPException, BackgroundTasks, Body  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]

# Import route modules
from main.api.ussd import router as ussd_router
from main.api.telematics import router as telematics_router

# Import centralized connection manager for WebSocket handling
from sockets.connection_manager import manager

# Import QR fleet generator script utility
from main.api.utils.fleet_generator import auto_generate_fleet_assests

# 1.Initialize the Single master instance
app = FastAPI(title="TaxiFare™ Telematic API", version="1.0.0")

# (Optional) CORS Middleware for cross-origin requests (HTML frontend can talk to API)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# 2.Mount isolated modules cleanly
app.include_router(telematics_router)
app.include_router(ussd_router)

# Request schema model for mounting QR system
# Use a plain request body dict to avoid a hard dependency on pydantic in environments
# where the package may not be resolvable by the editor/IDE. Validation is done manually.

# 3. ----- QR FLEET COUPLING (QR Code Engine Integration) -----
@app.post("/fleet/register", status_code=status.HTTP_201_CREATED, tags=["Fleet Management"])
async def register_vehicle_and_generate_qrs(vehicle: dict = Body(...), background_task: BackgroundTasks = None):
    """
    Registers a new vehicle and generates the complete set of topographical
    QR codes stickers for every single seat as a non-blocking background task.
    """
    # Basic validation
    vehicle_id = vehicle.get("vehicle_id")
    seat_count = vehicle.get("seat_count")

    if not vehicle_id or not isinstance(seat_count, int) or seat_count <= 0:
        raise HTTPException(status_code=400, detail="Invalid vehicle identity profile.")

    # Run QR generation logic as a background task to keep the API extremely fast
    if background_task is None:
        # Fallback: run synchronously if BackgroundTasks wasn't injected (shouldn't happen in normal FastAPI use)
        auto_generate_fleet_assests(vehicle_id, seat_count)
    else:
        background_task.add_task(auto_generate_fleet_assests, vehicle_id, seat_count)

    return {
        "status": "registration_initiated",
        "message": f"Fleet assets and seat sticker generation started for taxi: {vehicle_id}"
    }

# 4. ------ CORE HEALTH CHECKS ---------
@app.get("/ping", tags=["Health Check"])
async def ping():
    return {"status": "alive", "platform": "TaxiFare™ Core"}

# 5. ----- GLOBAL WEBSOCKET Engine (Driver Dashboard Streaming) -------
@app.websocket("/ws/fleet/{vehicle_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    vehicle_id: str
):
    await manager.connect(vehicle_id, websocket)

    try:
        while True:
            # (Keep socket open to listen for client disconnects)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(vehicle_id, websocket)
