from fastapi import APIRouter, Form, Response, Depends  # type: ignore[import]
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore[import]
from sqlalchemy import select, update  # type: ignore[import]

from ..database_src.database import get_db  # type: ignore[import]
from ..database_src.models import Commuter, Transaction, Vehicle  # type: ignore[import]
from ..database_src.repository import get_or_create_commuter, get_or_create_vehicle, create_transaction, get_recent_rides

# Import connection manager workspace instance
from ..sockets.connection_manager import manager

# Changed from FastAPI() to APIRouter() to allow for modular routing and mounting in the main application
router = APIRouter(prefix="/ussd", tags=["TaxiFare™ USSD Gateway"])

# # Mock database tracking wallet balances by phone number
# # Currency in SOuth African Rand (ZAR)
# MOCK_WALLET_DB: Dict[str, dict] = {
#     "+27831234567": {"name": "Sipho", "balance": 145.50}, 
#     "+27829876543": {"name": "Lerato", "balance": 22.00}
# }

# # Mock database logging passenger transit histories by phone number
# MOCK_RIDE_HISTORY_DB: Dict[str, List[dict]] = {
#     "+27831234567": [
#         {"date": "16/07", "route": "Bree -> Randburg", "fare": "R22.00"}, 
#         {"date": "17/07", "route": "Baragwanath -> Bree", "fare": "R25.00"}
#     ],
#     "+27829876543": [
#         {"date": "15/07", "route": "Bree -> Midrand", "fare": "R36.00"}
#     ]
# }

def lookup_vehicle(session_id: str) -> str:
    """
    Temporary lookup function, mapping a session to a physical vehicle.
    Synchronized precisely with our driver HTML client view keys.
    Replace this with a database lookup later.
    """
    return "bree-quantum-xyz-789"



# ---- INCLUSIVITY FALLBACK CAPABILITY (PASSENGER INTERFACE) ----
@router.post("")
@router.post("/ussd")
async def ussd_handler(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: Optional[str] = Form(""),   # Changed From(...) to Form("") to accept the initial dial empty string
    db: AsyncSession = Depends(get_db)  # Inject the database session for async operations
):
    # Fetch or auto-provision commuter record via Repository
    commuter = await get_or_create_commuter(db, phoneNumber)

    # Split the input text to determine menu depth
    text_segments = text.split("*") if text else []
    level = len(text_segments)

    # --------- Level 0 ---------------------
    # Initial Menu: User just dialed the code (Entry Point)
    if level == 0:
        response_text = (
            "CON Welcome to TaxiFare™\n"
            "1. Pay for My Seat\n"
            "2. Check Wallet Balance\n"
            "3. View Ride History\n"
            "4. Help\n"
            "5. Exit"
        )

    #----------- LEVEL 1 -----------------------
    # User selected an option from the main menu
    elif level == 1:
        selection = text_segments[0]
        if selection == "1":
            response_text = "CON Enter Seat Number(1-14):"
        
        elif selection == "2":
            # Dynamic Wallet Balance Engine Lookups via PostgreSQL
            formatted_balance = f"R{commuter.wallet_balance:.2f}"
            response_text = (
                f"END Hello {commuter.name}.\n"
                f"Your current TaxiFare™ wallet balance is: {formatted_balance}"
            )
        elif selection == "3":
            # Dynamic Ride History Engine Lookup via repository
            trips = await get_recent_rides(db, commuter.id, limit=3)
            
            if not trips:
                response_text = ("END No recent rides found associated with this mobile profile.")
            else:
                response_text = ("END Your Recent Rides:\n")
                for i, (tx, vehicle) in enumerate(trips, 1):
                    date_str = tx.created_at.strftime("%d/%m")
                    response_text += f"{i}. {date_str} {vehicle.license_plate} (Seat {tx.seat_number} - R{tx.amount:.2f}\n)"

        elif selection == "4":
            response_text = ("END For assistance contact TaxiFare™ Support.")

        elif selection == "5":
            response_text = ("END Thank You for using TaxiFare™.")

        else:
            response_text = ("END Invalid selection. Please try again.")

    #----------- LEVEL 2 --------------------
    # User entered a seat number after selecting "Pay for My Seat"
    elif level == 2:
        seat_number = text_segments[1]
        
        if not seat_number.isdigit():
            return Response(
                content="END Invalid seat number.",
                media_type="text/plain"
            )
                            
        if not (1 <= int(seat_number) <= 14):
            response_text = "END Seat number must be between 1 and 14."
        else:
            response_text = (
                f"CON Select Payment Method for Seat {seat_number}:\n"
                "1. MTN MoMo\n"
                "2. Linked Bank Account")

    #---------- LEVEL 3 ---------------------
    # User selected a payment method (Payment Orchestration and Socket State Dispatch)
    elif level == 3:
        seat_number = text_segments[1]
        payment_method = text_segments[2]
        
        if payment_method == "1":
            method_name = "MTN MoMo"
        elif payment_method == "2":
            method_name = "Linked Bank Account"
        else:
            return Response(content="END Invalid payment method selected.", media_type="text/plain")
        
        # Pull accurate registration key(we lookup  by route)
        target_taxi_id = lookup_vehicle(sessionId)
        
        # 2. Fetch or auto-provision record via Repository
        vehicle = await get_or_create_vehicle(
            db=db, 
            fleet_id=target_taxi_id, 
            license_plate="ND 351-654", 
            total_seats=14
        )
    
        # 3. Record transaction entry in PostgreSQL via Repository
        new_transaction = await create_transaction(
            db=db,
            commuter_id=commuter.id,
            vehicle_id=vehicle.id, 
            seat_number=int(seat_number),
            amount=22.00,   #Standard fare baseline for that route
            payment_method=method_name,
            status="PENDING"
        )

        # --- WEB-SOCKET REAL-TIME BROADCAST TRIGGER ---
        # Fire a background broadcast to immediately alert the drivers display app
        # via open WebSocket stream channels before Electrum fully closes the session
        await manager.broadcast_seat_update(
            vehicle_id=target_taxi_id,
            seat_id=int(seat_number),
            amount=float(new_transaction.amount),
            tx_id=str(new_transaction.id),
            status="PAID")

        response_text = (
            f"END Payment Request sent!\n"
            f"You will receive a prompt on your screen to authorise payment "
            f"for Seat {seat_number} via {method_name}."
        )
    #----------- UNKNOWN STATE ---------
    else:
        response_text = "END Invalid option selected. Please try again."

    return Response(content=response_text, media_type="text/plain")

