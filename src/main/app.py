import asyncio
from contextlib import asynccontextmanager   # type: ignore[import]

from fastapi import FastAPI, BackgroundTasks, Body, HTTPException, WebSocket, WebSocketDisconnect, status, Request  # type: ignore[import]
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from sqlalchemy import text     # type: ignore[import]
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.main.core.verifynow_gateway import validate_vehicle_registration
from src.main.core.security import router as security_router
from src.main.api.payments import router as payments_router
from src.main.api.notification import router as notification_router # type: ignore[import]
from src.main.schemas.electrum_events import ErrorDetail
from src.main.workers.offline_queue import process_offline_transactions

from .api.ussd import router as ussd_router
from .api.telematics import router as telematics_router
from .api.simulate_ussd import router as simulate_ussd_router
from .api.electrum_events import router as electrum_events_router

from .database_src.database import async_engine   # type: ignore[import]
from .database_src.redis import redis_client      # type: ignore[import]
from .sockets.connection_manager import manager
from .utils.fleet_generator import auto_generate_fleet_assets
from .utils.rate_limiter import limiter

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

    # 3. Start background worker for offline queue processing
    queue_worker_task = asyncio.create_task(process_offline_transactions())

    yield   # Application runs while suspended here

    # ----- SHUTDOWN LIFECYCLE -----
    # Cancel the background worker cleanly
    queue_worker_task.cancel()
    try: 
        await queue_worker_task
    except asyncio.CancelledError:
        pass

    # Close Redis connection pool cleanly
    await redis_client.aclose()
    print("[INFO] Redis connection pool closed cleanly.")

app = FastAPI(title="TaxiFare™ Telematic API", version="1.0.0", lifespan=lifespan)

# Rate Limiter Configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registrations
app.include_router(electrum_events_router)
app.include_router(payments_router)
app.include_router(notification_router)
app.include_router(telematics_router)
app.include_router(ussd_router)
app.include_router(security_router)
app.include_router(simulate_ussd_router)

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
@limiter.limit("10/minute")
async def register_vehicle_and_generate_qrs(request: Request, background_tasks: BackgroundTasks, vehicle: dict = Body(...)):
    vehicle_id = vehicle.get("vehicle_id")
    seat_count = vehicle.get("seat_count")
    registration_number = vehicle.get("registration_number")
    vin = vehicle.get("vin")

    if not vehicle_id or not isinstance(seat_count, int) or seat_count <= 0:
        raise HTTPException(status_code=400, detail="Invalid vehicle identity profile.")
    
    if not registration_number or not vin:
        raise HTTPException(status_code=400, detail="Registration number and VIN are required for compliance validation.")

    # 1. Validate vehicle legally exists and is roadworthy before onboarding
    validation_result = await validate_vehicle_registration(registration_number, vin)
    
    # 2. Queue fleet asset generation in the background
    background_tasks.add_task(auto_generate_fleet_assets, vehicle_id, seat_count)

    return {
        "status": "registration_initiated",
        "message": f"Fleet assets and seat sticker generation started for taxi: {vehicle_id}",
        "compliance_data": validation_result
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors into Elertrum's ErrorDetail schema for events routes."""
    if request.url.path.startswith("/payments/events-api/v1"):
        first_error = exc.errors()[0] if exc.errors() else {}
        loc = " -> ".join(str(l) for l in first_error.get("loc", []))
        msg = first_error.get("msg", "Invalid payload format")

        error_detail = ErrorDetail(
            schema="ErrorDetail",
            message="Request validation failed",
            detail=f"{loc}: {msg}"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, 
            content=error_detail.model_dump(by_alias=True)
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


@app.get("/ping", tags=["Health Check"])
async def ping(request: Request):
    return {"status": "alive", "platform": "TaxiFare™ Core"}
