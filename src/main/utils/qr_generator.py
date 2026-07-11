import qrcode
import json
import os
import time

def generate_taxi_seat_qr(vehicle_id: str, seat_number: int, save_path: str = "assets/qr_codes"):
    """
    Generates a unique QR code for a specific taxi seat inside a specified vehicle.
    The QR encodes a JSON payload that the Commuter Mobile App reads when scanned.
    """
    # 1. Create data payload the commuter's phone will read upon scanning
    payload = {
        "app_identifier": "com.taxiapp.seatpayment",
        "vehicle_id": vehicle_id,
        "seat_number": seat_number,
        "timestamp": int(time.time()),  # Optional: for added security/validation
    }
    # Convert payload to string format
    payload_string = json.dumps(payload)


    # 2. Configure the QR code parameters/settings
    qr = qrcode.QRCode(
        version = 1,  # Controls the size of the QR code (1-40)
        error_correction = qrcode.ERROR_CORRECT_M,  # Medium error tolerance for scratches/damage in the taxi
        box_size = 10,  # Size of each box in pixels
        border = 4,  # Thickness of the border (default is 4)  
    )
    qr.add_data(payload_string)
    qr.make(fit=True)

    # 3. Render the image and save it to the specified path
    img = qr.make_image(fill_color="black", back_color="white")

    # Ensure save directory exists
    os.makedirs(save_path, exist_ok=True)

    # Save the QR code image with a unique filename
    filename = f"taxi_{vehicle_id}_seat_{seat_number}.png"
    full_file_path = os.path.join(save_path, filename)
    img.save(full_file_path)

    print(f"✓ QR Code generated successfully and saved to: {full_file_path}")
    return full_file_path

# ---- SIMULATE GENERATION ------
if __name__ == "__main__":
    # Mocking a Toyota Quantum Vehicle UUID from database
    sample_taxi_uuid = "e8b2a5c4-1234-5678-abcd-ef1234567890"

    print("Generating sticker QR coded for a 16-seater moring rush-hour commut...")
    # Generate QR codes for the first 3 seats as a test
    for seat in range(1, 4):
        generate_taxi_seat_qr(vehicle_id = sample_taxi_uuid, seat_number = seat)