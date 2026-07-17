from fastapi import FastAPI, BackgroundTasks, Body, HTTPException, WebSocket, WebSocketDisconnect, status  # type: ignore[import]
from .utils.fleet_generator import auto_generate_fleet_assets
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]

from .api.ussd import router as ussd_router
from .api.telematics import router as telematics_router
from .sockets.connection_manager import manager


app = FastAPI(title="TaxiFare™ Telematic API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telematics_router)
app.include_router(ussd_router)


@app.websocket("/ws/fleet/{vehicle_id}")
async def websocket_fleet_endpoint(websocket: WebSocket, vehicle_id: str):
    await manager.connect(vehicle_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(vehicle_id, websocket)


@app.post(
        "/fleet/register", 
        status_code=status.HTTP_201_CREATED, 
        tags=["Fleet Management"], 
        response_model=None)

async def register_vehicle_and_generate_qrs(vehicle: dict = Body(...), background_task= None):
    vehicle_id = vehicle.get("vehicle_id")
    seat_count = vehicle.get("seat_count")

    if not vehicle_id or not isinstance(seat_count, int) or seat_count <= 0:
        raise HTTPException(status_code=400, detail="Invalid vehicle identity profile.")
    
    # Stanadard import inside the function to safeguard the execution context
    from fastapi import BackgroundTasks as FastAPIBackgroundTasks # type: ignore[import]

    # If FastAPI fails to inject it natively due to environment type mismatches, initialize manually
    if background_task is None:
        background_task = FastAPIBackgroundTasks()

    # Pass background tasks execution utilizing exact dictionary key reading syntax
    background_task.add_task(auto_generate_fleet_assets, vehicle_id, seat_count)

    return {
        "status": "registration_initiated",
        "message": f"Fleet assets and seat sticker generation started for taxi: {vehicle_id}",
    }


@app.get("/ping", tags=["Health Check"])
async def ping():
    return {"status": "alive", "platform": "TaxiFare™ Core"}
