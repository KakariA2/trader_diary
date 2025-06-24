CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    subscription_status TEXT NOT NULL DEFAULT 'free',  -- free, trial, premium
    trial_start_date TEXT,  -- в формате YYYY-MM-DD
    premium_end_date TEXT   -- в формате YYYY-MM-DD
);