import logging

from fastapi import APIRouter, BackgroundTasks, status, Request 
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from sqlalchemy import select

from src.main.schemas.electrum_events import ElectrumEventPayload
from src.main.database_src.database import AsyncSessionLocal
from src.main.database_src.models import Transaction
from src.main.sockets.connection_manager import manager

class ErrorDetail(BaseModel):
    schema: str
    message: str
    detail: str

logger = logging.getLogger("electrum_events")
router = APIRouter(prefix="/payments/events-api/v1", tags=["Electrum Events"])

# Known failure and rejection event types defined in the Electrum event lifecycle
REJECTION_EVENT_TYPES = {
    "CREDIT_AUTH_REJECTED",
    "RTC_INBOUND_CREDIT_AUTH_REJECTED",
    "CREDIT_AUTH_TIMEOUT"
    "CREDIT_AUTH_DECLINED",
    "CREDIT_AUTH_DECLINED_NACK",
    "CREDIT_COMPLETION_REJECTED",
    "RTC_INBOUND_CREDIT_AUTH_VALIDATION_FAILED",
    "RTC_INBOUND_CREDIT_AUTH_VALIDATION_TIMEOUT",
}

SUCCESS_EVENT_TYPES = {
    "CREDIT_AUTH_RECEIVED",
    "CREDIT_AUTH_ACCEPTED",
    "RTC_INBOUND_CREDIT_AUTH_ACCEPTED",
    "RTC_INBOUND_CREDIT_AUTH_APPROVED",
    "CREDIT_COMPLETION_ACCEPTED",
    "RTC_INBOUND_CREDIT_AUTH_VALIDATION_SUCCESS",
}


async def handle_transaction_events(event: ElectrumEventPayload):
    """Processes transaction lifecycle state changes and updates local ledgers."""
    uetr = event.tranInfo.tranUetr if event.tranInfo else None
    event_type = event.type or event.name

    if not uetr:
        logger.warning(f"Skipping event {event.name}: No tranUetr present in tranInfo.")
        return

    try:
        async with get_async_session() as db_session:
            # Locate transaction by external refernce/UETR
            stmt = select(Transaction).where(Transaction.external_provider_refernce == uetr)
            result = await db_session.execute(stmt)
            tx = result.scalar_one_or_none()

            if not tx:
                logger.error(f"Transaction with UETR {uetr} not found in database.")
                return
            
            if event_type in SUCCESS_EVENT_TYPES:
                tx.payment_status = "COMPLETED"
                await db_session.commit()

                # Notify driver terminal 
                await manager.broadcast_seat_update(
                    vehicle_id=str(tx.vehicle_id),
                    seat_id=tx.seat_number,
                    amount=float(tx.amount),
                    tx_id=str(tx.id),
                    status="PAID"
                )
                logger.info(f"Transaction {tx.id} marked COMPLETED via event {event_type}.")

            elif event_type in REJECTION_EVENT_TYPES:
                tx.payment_status = "FAILED"
                await db_session.commit()

                # Notify driver and passenger of payment failure
                await manager.broadcast_seat_update(
                    vehicle_id=str(tx.vehicle_id),
                    seat_id=tx.seat_number,
                    amount=float(tx.amount),
                    tx_id=str(tx.id),
                    status="PAYMENT_FAILED"
                )
                logger.warning(f"Transaction {tx.id} marked FAILED via rejection event {event_type}.")

    except Exception as db_err:
        logger.error(f"Database update failed while processing event {event.name}: {db_err}")


@router.post(
    "/events", 
    status_code=status.HTTP_200_OK, 
    responses= {
        400: {"model": ErrorDetail, "description": "Bad Request"},
        500: {"model": ErrorDetail, "description": "Internal Server Error"},
    }
)

async def receive_electrum_event(event: ElectrumEventPayload, background_tasks: BackgroundTasks):
    """
    Ingests Electrum events, returning HTTP 200 OK immediately and handling processing in the background. 
    """
    try:
        # Validate that the event has a valid discriminator/ class[cite: 2]
        if not event.event_class and not event.name:
            error_response = ErrorDetail(
                schema="ErrorDetail",
                message="Invalid event payload",
                detail="Missing required 'class' or name event identifier."
            )
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=error_response.model_dump(by_alias=True))

        background_tasks.add_task(handle_transaction_events, event)
        return {"status": "ACKNOWLEDGED", "eventId": event.name}

    except Exception as exc:
        logger.error(f"Unexpected error processing Electrum webhook: {exc}", exc_info=True)
        error_response = ErrorDetail(
            schema="ErrorDetail",
            message="Internal server error processing event",
            detail=str(exc)
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response.model_dump(by_alias=True))