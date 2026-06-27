import requests
import json

# The local URL where our FastAPI app runs
USSD_URL = "http://127.0.0.1:8000/ussd"

def simulate_ussd_step(session_id: str, phone: str, text_input: str):
    """ Sends a mocked HTTP POST payload matching Africa's Talking format."""
    payload = {
        "sessionId": session_id,
        "serviceCode": "*120*1234#",
        "phoneNumber": phone,
        "text": text_input
    }

    # Afrcia's Talking sends data as form-urlencoded, not JSON
    response = requests.post(USSD_URL, data=payload)
    return response.text

def run__full_session_simulation():
    session_id = "session_bree_rank_999"
    commuter_phone = "+27831234567"

    print("====================================================")
    print("🚀 STARTING TAXIFARE™ USSD LIFECYCLE SIMULATION")
    print("====================================================")


    # Step 1: User dials the string *120*1234#
    print("\n[Step 1] Commuter dials *120*1234#")
    current_input = ""
    replay = simulate_ussd_step(session_id, commuter_phone, current_input)
    print(f"Network Response:\n{replay}")
    
    # Step 2: User inputs '1' to select "Pay for My Seat"
    print("\n[Step 2] Commuter enters '1' (Pay for My Seat)")
    current_input = "1"
    replay = simulate_ussd_step(session_id, commuter_phone, current_input)
    print(f"Network Response:\n{replay}")

    # Step 3: User inputs '4' to pick Seat Number 4
    print("\n[Step 3] Commuter enters '4' (Seat 4)")
    current_input = "1*4"
    replay = simulate_ussd_step(session_id, commuter_phone, current_input)
    print(f"Network Response:\n{replay}")

    # Step 4: User inputs '1' to select MTN MoMo or Vodacom VodaPay as their gateway path
    print("\n[Step 4] Comuuter enters '1' (Confirm via MTN MoMo or Vodacom VodaPay)")
    current_input = "1*4*1"
    replay = simulate_ussd_step(session_id, commuter_phone, current_input)
    print(f"Network Response:\n{replay}")
    print("=======================================================")


if __name__ == "__main__":
    try:
        run__full_session_simulation()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Your FastAPI server isn't running!")
        print("Please run: uvicorn src.api.ussd:app --reload -- 8000")
