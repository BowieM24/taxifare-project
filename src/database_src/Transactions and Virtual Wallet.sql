-- 1. Commuter Profiles
CREATE TABLE commuters (
    commuter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    pin_hash TEXT NOT NULL, -- For the 2FA mentioned in your diagram
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Digital Wallets (The "Spending Tracker" source)
CREATE TABLE wallets (
    wallet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commuter_id UUID REFERENCES commuters(commuter_id),
    balance DECIMAL(10, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'ZAR',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Transactions (The data for your Spending Tracker)
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commuter_id UUID REFERENCES commuters(commuter_id),
    taxi_id VARCHAR(50), -- Link to the taxi vehicle
    seat_id INT,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(20), -- 'Bank', 'MoMo', 'VodaPay', 'USSD'
    status VARCHAR(20), -- 'Pending', 'Approved', 'Declined'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);