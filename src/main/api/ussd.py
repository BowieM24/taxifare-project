from fastapi import APIRouter, Form, Response, HTTPException  # type: ignore[import]
from typing import Dict
# Import connection manager workspace instance
from ..sockets.connection_manager import manager

# Changed from FastAPI() to APIRouter() to allow for modular routing and mounting in the main application
router = APIRouter(tags=["TaxiFare™ USSD Engine"])

# Mock database tracking wallet balances by phone number
# Currency in SOuth African Rand (ZAR)
MOCK_WALLET_DB: Dict[str, dict] = {
    "+27831234567": {"name": "Sipho", "balance": 145.50}, 
    "+27829876543": {"name": "Lerato", "balance": 22.00}
}

def lookup_vehicle(session_id: str) -> str:
    """
    Temporary lookup function, mapping a session to a physical vehicle.
    Synchronized precisely with our driver HTML client view keys.
    Replace this with a database lookup later.
    """
    return "bree-quantum-xyz-789"



# ---- INCLUSIVITY FALLBACK CAPABILITY (PASSENGER INTERFACE) ----
@router.post("/ussd")
async def ussd_handler(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form("")   # Changed From(...) to Form("") to accept the initial dial empty string
):
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
            # Dynamic Wallet Balance Engine Lookups
            user_profile = MOCK_WALLET_DB.get(phoneNumber)
            if user_profile:
                name = user_profile["name"]
                balance = user_profile["balance"]
                response_text = f"END Hello {name}.\nYour current TaxiFare™ wallet balance is: R{balance:.2f}"
            else:
                response_text = ("END Your phone number is not registered. Please sign up via the TaxiFare™ App.")
        elif selection == "3":
            response_text = ("END Ride history is not available yet.")

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
            response_text = (f"CON Select Payment Method for Seat {seat_number}:\n"
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
        
        # --- WEB-SOCKET REAL-TIME BROADCAST TRIGGER ---
        # Fire a background broadcast to immediately alert the drivers display app
        # via open WebSocket stream channels before Electrum fully closes the session
        await manager.broadcast_seat_update(
            vehicle_id=target_taxi_id,
            seat_number=int(seat_number),
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

