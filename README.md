# TaxiFare

**Digital Payment Solution for Minibus Taxi Transport**

TaxiFare is a comprehensive digital payment and management system designed to modernize minibus taxi operations across South Africa. By replacing cash-based fare collection with secure QR code and USSD payments, TaxiFare eliminates theft risks, improves operational efficiency, and provides real-time transaction data for better planning and growth.

## Documentation

- **[Flow Diagram](./TaxiFare_flow_diagram_.pdf)** - System architecture and process flow
- **[Presentation](./TaxiFare_BeOrchid_Presentation.pptx)** - Project overview and key features
- **[Development Roadmap](./Developement_roadmap.docx)** - Project timeline and milestones

## Features

- **QR Code Payment System** - Every seat in the minibus has a designated QR code for seamless fare collection
- **USSD Integration** - Commuters are directed to their banking app to approve transactions with a temporary PIN
- **Real-time Seat Status** - Driver dashboard displays seat availability in real-time (green for available)
- **Digital Transaction Receipts** - SMS receipts sent to commuters for every transaction
- **Commuter Profiles** - Track commuter history and transaction data
- **Revenue Analytics** - Comprehensive trip and revenue data for planning and growth

## System Architecture

TaxiFare consists of three main components:

1. **Mobile App** - Commuter-facing application for QR scanning and payment approval
2. **Backend** - Core system handling payment processing, data management, and real-time updates
3. **Driver/Merchant Dashboard** - Driver interface for seat management and trip monitoring

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|----------|
| **Frontend (Mobile)** | React Native or Flutter | Cross-platform (iOS/Android) with excellent QR scanning and USSD libraries |
| **Backend** | Node.js (Express) or Python (FastAPI) | High performance for processing TaxiFare transactions |
| **Database** | PostgreSQL | Relational database for commuter profiles and transaction receipts |
| **Real-time Updates** | Socket.io or Firebase | Instant seat status updates on driver dashboard |
| **Payments/SMS** | Stitch/Ozow & Twilio | South African bank-to-bank (EFT) payments and SMS receipts |

## Use Cases & Problem Statement

**Market Context:**
- Over 15 million commuters daily rely on minibus transport (vital to national transport infrastructure)
- Current cash-based system causes delays, theft risks, and data gaps
- Lack of reliable trip and revenue data hinders planning and growth

**TaxiFare Solution:**
- Eliminates manual cash handling and associated risks
- Provides real-time transaction data for better planning
- Improves operational efficiency and revenue tracking
- Enhances commuter experience with digital receipts

## Installation

### Prerequisites
- Node.js 16+ or Python 3.8+
- PostgreSQL 12+
- Git

### Backend Setup

```bash
# Clone the repository
git clone https://gitlab.com/taxifare/taxifare-project.git
cd taxifare-project

# Install dependencies
npm install  # For Node.js
# or
pip install -r requirements.txt  # For Python

# Configure environment variables
cp .env.example .env

# Run database migrations
npm run migrate  # For Node.js
# or
python manage.py migrate  # For Python

# Start the server
npm start  # For Node.js
# or
python app.py  # For Python
```

### Mobile App Setup

Refer to the mobile app repository for React Native or Flutter setup instructions.

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a merge request

### Code Standards
- Follow the existing code style
- Write clear commit messages
- Add tests for new features
- Update documentation as needed

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please:
- Open an issue on GitLab
- Contact the development team
- Review the documentation files above
