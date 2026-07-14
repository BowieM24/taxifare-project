
import requests
import time

URL = "http://127.0.0.1:8000/telematics/seat-update"
VEHICLE = "bree-quantum-xyz-789"

def send_telemetry_packet(seat: int, variance: float):
    payload = {
        "vehicle_id": VEHICLE,
        "seat_number": seat,
        "accel_variance": variance,
        "accel_magnitude": 9.81
    }
    try:
        response = requests.post(URL, json=payload)
        return response.json()
    except requests.exceptions.ConnectionError:
        return None

def run_telematics_simulation():
    print("==========================================================")
    print("🛰️  RUNNING TAXIFARE™ SENSOR FUSION VALIDATION LIFECYCLE")
    print("==========================================================")

    print("\n[Scenario 1] Taxi driving smoothly on open road...")
    for _ in range(2):
        print("  Stream payload: S1=3.2, S2=2.9, S3=3.5")
        send_telemetry_packet(1, 3.2)
        send_telemetry_packet(2, 2.9)
        send_telemetry_packet(3, 3.5)
        time.sleep(0.5)

    print("\n[Scenario 2] Taxi encounters traffic gridlock (All nodes drop flat)...")
    for _ in range(2):
        res = send_telemetry_packet(1, 0.05)
        send_telemetry_packet(2, 0.04)
        send_telemetry_packet(3, 0.06)
        print(f"  Server State: {res}")
        time.sleep(0.5)

    print("\n[Scenario 3] Taxi moves away, but Seat 1 gets off (Divergence)...")
    for step in range(1, 5):
        res = send_telemetry_packet(1, 0.02) 
        send_telemetry_packet(2, 3.8)
        send_telemetry_packet(3, 4.1)
        print(f"  Step {step}/4 for Seat 1 evaluation output -> {res}")
        time.sleep(0.2)

if __name__ == "__main__":
    run_telematics_simulation()
