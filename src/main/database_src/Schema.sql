-- ====================================================================
-- TAXIFARE PLATFORM - DATABASE SCHEMA
-- Location: src/database/schema.sql
-- ====================================================================

-- Enable UUID extension (Required for automated random IDs in PostgreSQL)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. COMMUTER PROFILES
CREATE TABLE commuters (
    commuter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    pin_hash TEXT NOT NULL, -- For the 2FA authentication prompt
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. DIGITAL WALLETS (Feeds the Spending Tracker metrics)
CREATE TABLE wallets (
    wallet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commuter_id UUID REFERENCES commuters(commuter_id) ON DELETE CASCADE,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'ZAR',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. VEHICLES (Toyota Quantum 16-seater vs VW Crafter 22-seater layouts)
CREATE TABLE vehicles (
    vehicle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_plate VARCHAR(15) UNIQUE NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL, -- Matches 'toyota_quantum_16' or 'vw_crafter_22' config keys
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. DRIVERS
CREATE TABLE drivers (
    driver_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    assigned_vehicle_id UUID REFERENCES vehicles(vehicle_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. SEATS (The live state engine for the Driver's Topographical Dashboard)
CREATE TABLE seats (
    seat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    seat_number INT NOT NULL, -- e.g., 1, 2, 3...
    is_paid BOOLEAN DEFAULT FALSE, -- Flips to TRUE when Electrum webhook returns SUCCESS
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vehicle_id, seat_number) -- Prevents assigning two Seat 4s inside the same taxi
);

-- 6. TRANSACTIONS (Historical record for payment verification and user ledger)
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commuter_id UUID REFERENCES commuters(commuter_id) ON DELETE SET NULL,
    vehicle_id UUID REFERENCES vehicles(vehicle_id) ON DELETE SET NULL,
    seat_number INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(20), -- 'ELECTRUM_MOMO', 'ELECTRUM_VODAPAY', 'USSD', etc.
    status VARCHAR(20), -- 'PENDING', 'APPROVED', 'DECLINED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);