import os
import json
import qrcode
import time
# import psycopg2 # Uncomment in production when connect to real database

# Mock Database Connection for local testing with PostgreSQL (Replace with actual connection in production)/ without spinning up PGAdmin
class MockDBConnection:
    def execute(self, query, params):
        print(f"SQL EXECUTE: {query} with values {params}")
    def fetchone(self, query, params):
        # Simulating that we found the vehicle configuration in the database
        return ("toyota_quantum_16",)  # Returning a tuple as if it were a real DB response

    
def get_vehicle_capacity(vehicle_type: str) -> int:
    """
    Returns the total passanger seaats based on the vehicle type schema."""

    if "16" in vehicle_type:
        return 13   # 16-seater quantum has 13 passenger seats (excluding driver and front passenger)
    elif "22" in vehicle_type:
        return 19   # 22-seater crafter has 19 passenger seats
    return 15


def generate_taxi_seat_qr(vehicle_id: str, seat_number: int, save_path: str = "assets/qr_codes"):
    """Your proven QR code builder script."""
    payload = {
        "app_identifier": "com.taxiapp.seatpayment",
        "vehicle_id": vehicle_id,
        "seat_number": seat_number,
        "timestamp": int(time.time()),
    }
    qr = qrcode.QRCode(
        version = 1,
        error_correction = qrcode.ERROR_CORRECT_M,
        box_size = 10,
        border = 4,
    )
    qr.add_data(json.dumps(payload))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    filename = f"taxi_{vehicle_id}_seat_{seat_number}.png"
    full_file_path = os.path.join(save_path, filename)
    img.save(full_file_path)
    return full_file_path


def auto_generate_fleet_assets(vehicle_id: str):
    """
    1. Looks up the vehicle type in the database.
    2. Registers every individual seat in the SQL 'seats' table.
    3. Bulk exports the scannable sticker image files.
    """
    db = MockDBConnection()
    save_path = f"assets/qr_codes/{vehicle_id}"
    os.makedirs(save_path, exist_ok=True)

    # Step 1: Fetch vehicle type and capacity from DB
    # In production: cursor.execute("SELECT vehicle_type FROM vehicle WHERE id = %s", (vehicle_id,))
    vehicle_type = db.fetchone("SELECT vehicle_type FROM vehicle WHERE id = %s", (vehicle_id,))[0]
    capacity = get_vehicle_capacity(vehicle_type)
    print(f"▶ Starting bulk generation for Vehicle ID: {vehicle_id} ({vehicle_type})")

    # Steps 2: Loop through every seat, insert into DB and build the QR
    for seat_num in range(1, capacity + 1):
        # 1. Write the state to the relational database 'seats' table
        db.execute(
            "INSERT INTO seats (vehicle_id, seat_number, status) VALUES (%s, %s, FALSE) ON CONFLICT DO NOTHING;",
            (vehicle_id, seat_num)
        )

        # 2. Generate the actual file
        file_generated = generate_taxi_seat_qr(vehicle_id, seat_num, save_path)
        print(f"✓ Seat #{seat_num} registered and QR code generated at: {file_generated}")

    print(f"🏁 Fleet initialization complete! All sticker assets saved under: {save_path}\n")

# ---- SIMULATE REGISTERING A NEW TAXI ---
if __name__ == "__main__":
    # Image a driver just registered their new Toyota Quantum 16-seater at the Bree Street Taxi Rank
    new_quantum_uuid = "bree_quantum-xyz-789"
    auto_generate_fleet_assets(vehicle_id = new_quantum_uuid)