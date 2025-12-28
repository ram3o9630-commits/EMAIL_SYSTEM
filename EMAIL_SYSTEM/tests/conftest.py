import os
import pytest
import sqlite3

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in [
        "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD",
        "SMTP_USE_TLS", "SMTP_USE_SSL", "FROM_EMAIL", "FROM_NAME", "DB_URL"
    ]:
        monkeypatch.delenv(var, raising=False)

@pytest.fixture
def smtp_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("FROM_EMAIL", "no-reply@test.local")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("DB_URL", "sqlite:///:memory:")

@pytest.fixture
def temp_db():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL,
        name TEXT NOT NULL,
        subscription_status TEXT,
        last_payment_date TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS email_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        email_type TEXT,
        status TEXT,
        error_message TEXT,
        timestamp TEXT
    )''')
    cur.execute('''INSERT INTO users (id, email, name, subscription_status, last_payment_date)
                  VALUES (?, ?, ?, ?, ?)''',
                (1, "user1@test.local", "User One", "active", "2025-12-01"))
    conn.commit()
    yield conn
    conn.close()

@pytest.fixture
def demo_user():
    return {
        "id": 1,
        "email": "user1@test.local",
        "name": "User One",
        "subscription_status": "active",
        "last_payment_date": "2025-12-01"
    }
