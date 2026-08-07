from contextlib import asynccontextmanager   # type: ignore[import]
from fastapi import FastAPI, BackgroundTasks, Body, HTTPException, WebSocket, WebSocketDisconnect, status  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from sqlalchemy import text     # type: ignore[import]

from src.main.api.payments import router as payments_router
from src.main.api.notification import router as notification_router # type: ignore[import]
from .api.ussd import router as ussd_router
from .api.telematics import router as telematics_router
from .db.database import async_engine   # type: ignore[import]
from .db.redis import redis_client      #Import Redis client instance
from .sockets.connection_manager import manager
from .utils.fleet_generator import auto_generate_fleet_assets


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ------ STARTUP LIFECYCLE ------
    # 1. Validate PostgreSQL connection pool
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("[SUCCESS] PostgreSQL Connection pool initilized and verified.")
    except Exception as e:
        print(f"[FATAL] Database connection pool failed to initialize: {e}")

    # 2. Validate Redis connection
    try:
        await redis_client.ping()
        print("[SUCCESS] Redis Connection pool initialized and verified.")
    except Exception as e:
        print(f"[FATAL] Redis connection failed to initialize: {e}")

    yield   # Application runs while suspended here

    # ----- SHUTDOWN LIFECYCLE -----
    # Close Redis connection pool cleanly
    await redis_client.close()
    pint("[INFO] Redis connection pool closed cleanly.")

app = FastAPI(title="TaxiFare™ Telematic API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments_router)
app.include_router(notification_router)
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

async def register_vehicle_and_generate_qrs(vehicle: dict = Body(...), background_tasks: BackgroundTasks = None):
    vehicle_id = vehicle.get("vehicle_id")
    seat_count = vehicle.get("seat_count")

    if not vehicle_id or not isinstance(seat_count, int) or seat_count <= 0:
        raise HTTPException(status_code=400, detail="Invalid vehicle identity profile.")
    
    # If FastAPI fails to inject it natively due to environment type mismatches, initialize manually
    if background_tasks is None:
        background_tasks = BackgroundTasks()

    # Queue fleet asset generation in the background
    background_tasks.add_task(auto_generate_fleet_assets, vehicle_id, seat_count)

    return {
        "status": "registration_initiated",
        "message": f"Fleet assets and seat sticker generation started for taxi: {vehicle_id}",
    }


@app.get("/ping", tags=["Health Check"])
async def ping():
    return {"status": "alive", "platform": "TaxiFare™ Core"}
