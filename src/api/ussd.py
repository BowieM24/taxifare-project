from fastapi import FastAPI, Form, Response;

app = FastAPI(title="TaxiFare USSD Engine")

@app.post("/ussd")
async def ussd_handler(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(...)   # Contains user inputs separated by '*' e.g. "1*4"
):
    # Split the input text to determine menu depth
    text_segments = text.split("*") if text else []
    level = len(text_segments)

    # Initial Menu: User just dailed the code
    if level == 0:
        response_text = "CON Welcome to TaxiFare™\n"
        response_text = "1. Pay for My Seat\n"
        response_text = "2. Check Wallet Balance\n"
        response_text = "3. View Ride History\n"
        response_text = "4. Help\n"
        response_text = "5. Exit"

    
    # Level 1: User selected an option from the ain menu
    elif level == 1:
        selection = text_segments[0]
        if selection == "1":
            response_text = "CON Enter Seat Number(1-14):"
        elif selection == "2":
            # Mocking database balance retrieval for the user's phoneNumber
            response_text = "END Your current TaxiFare™ wallet balance is: R75.00"
        else:
            response_text = "END Invalid selection. Please try again."

    # Level 2: User enterd a seat number after selecting "Pay for My Seat"
    elif level == 2:
        seat_number = text_segments[1]
        # Store the seat number context or validate it
        response_text = f"CON Select Payment Method for Seat {seat_number}:\n"
        response_text += "1. MTN MoMo\n"
        response_text += "2. Linked Bank Account\n"

    # Level 3: User selected a payment method
    elif level == 3:
        payment_method = text_segments[2]
        seat_number = text_segments[1]

        method_name = "MTN MoMo" if payment_method == "1" else "Bank EFT"

        # Triggering the actual payment generation system background tasks here
        # Trigger_electrum_charge(phoneNumber, seat_number, payment_method)

        response_text = f"END Request sent! You will receive an prompt on your screen to authorise payment for Seat {seat_number} via {method_name}."

    else:
        response_text = "End Invalid option selected. Please again."
    
    # Africa's  talking requires plain text return format with a content-type header
    return Response(content = response_text, media_type = "text/plain")

