# TaxiFare Project

TaxiFare is a digital payment and fleet-management prototype for minibus taxi operations in South Africa. The current implementation focuses on a FastAPI backend that demonstrates QR-driven seat payment, USSD-based passenger interaction, and live seat updates through WebSockets for a driver dashboard simulation.

## What changed from the original plan

The original concept envisioned a broader product stack with a separate mobile app, a richer payment gateway, and a more formal database-backed backend. The current repository reflects a more focused prototype phase:

- The backend is implemented with FastAPI instead of a full Node.js or mobile-first stack.
- USSD payment flow and seat status updates are already wired to a simulated driver dashboard.
- QR code generation is local and file-based for fleet asset setup rather than fully integrated with a production database.
- Payment handling and notification behaviour are currently mocked or placeholder-based.
- The dashboard is a lightweight HTML simulation rather than a production web application.

## Current project structure

```text
taxifare-project/
├── src/
│   └── main/
│       ├── app.py
│       ├── api/
│       │   ├── ussd.py
│       │   ├── telematics.py
│       │   └── notification.py
│       ├── sockets/
│       │   └── connection_manager.py
│       ├── dashboard/
│       │   └── driver_dashboard_sim.html
│       ├── services/
│       │   ├── vehicle_service.py
│       │   └── payment_service.py
│       ├── models/
│       └── utils/
│           ├── fleet_generator.py
│           └── qr_generator.py
├── assets/
├── README.md
└── requirements.txt
```

## Core capabilities

- USSD payment flow for seat selection and payment method selection
- WebSocket-based seat status broadcasting to the dashboard simulation
- Telematics-inspired seat state evaluation for occupancy changes
- QR fleet asset generation for vehicle seat stickers
- A simple service layer for future expansion into real payment and vehicle persistence

## Run locally

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
cd taxifare-project
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt
```

### Start the API

```bash
uvicorn src.main.app:app --reload
```

### Useful endpoints

- GET /ping
- POST /ussd
- POST /telematics/seat-update
- GET /ws/fleet/{vehicle_id}
- POST /fleet/register

## Notes on implementation status

This repository is currently a functional prototype and not yet a production-ready deployment. The next natural steps are:

1. Replace simulated payment and notification flows with real provider integrations.
2. Introduce a persistent database layer for vehicles, seats, and transactions.
3. Expand the dashboard into a full real-time operational interface.
4. Add automated tests around the USSD, telematics, and socket workflows.

## License

This project is intended for prototype and demonstration purposes. Update the licensing terms before production use.

Verification Code:
WTC-FB8WBV9S
