-- Database: neobank

-- DROP DATABASE IF EXISTS neobank;
BEGIN;

-- CREATE DATABASE IF NOT EXISTS neobank
--     WITH
--     OWNER = postgres
--     ENCODING = 'UTF8'
--     LC_COLLATE = 'English_India.1252'
--     LC_CTYPE = 'English_India.1252'
--     LOCALE_PROVIDER = 'libc'
--     TABLESPACE = pg_default
--     CONNECTION LIMIT = -1
--     IS_TEMPLATE = False;

-- PostgreSQL schema for NeoBank API
-- Creates core tables: users, accounts, transactions, loans, beneficiaries

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(128),
    email VARCHAR(128) UNIQUE,
    phone VARCHAR(32),
    pin_hash VARCHAR(128),
    voice_embedding JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_type VARCHAR(32) NOT NULL,
    balance NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(8) NOT NULL DEFAULT 'USD',
    account_number VARCHAR(32) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description VARCHAR(256),
    amount NUMERIC(18,2) NOT NULL,
    type VARCHAR(16),
    category VARCHAR(64),
    status VARCHAR(32) DEFAULT 'completed'
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);

-- Loans table
CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    loan_type VARCHAR(64) NOT NULL UNIQUE,
    interest_rate NUMERIC(6,3) NOT NULL,
    min_amount BIGINT,
    max_amount BIGINT,
    tenure VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Beneficiaries
CREATE TABLE IF NOT EXISTS beneficiaries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    account_number VARCHAR(64) NOT NULL,
    bank_name VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_beneficiaries_user_id ON beneficiaries(user_id);

-- Optional Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(128) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed Loan Types (Optional)
INSERT INTO loans (loan_type, interest_rate, min_amount, max_amount, tenure)
VALUES
  ('personal', 5.5, 1000, 50000, '1-5 years'),
  ('home', 3.8, 50000, 500000, '5-30 years'),
  ('auto', 4.2, 5000, 75000, '1-7 years')
ON CONFLICT (loan_type) DO NOTHING;

COMMIT;