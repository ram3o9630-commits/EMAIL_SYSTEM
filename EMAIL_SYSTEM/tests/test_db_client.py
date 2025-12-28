import pytest
import no_reply_email_system
import sqlite3
from datetime import datetime

@pytest.fixture
def db_with_log_table(temp_db):
    cur = temp_db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS email_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        email_type TEXT,
        status TEXT,
        error_message TEXT,
        timestamp TEXT
    )""")
    temp_db.commit()
    yield temp_db

def test_get_user_by_id(temp_db, monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite:///:memory:")
    db = no_reply_email_system.SQLDataAccess()
    db.conn = temp_db
    user = db.get_user_by_id(1)
    assert user is not None
    assert user["email"] == "user1@test.local"
    assert user["name"] == "User One"
    assert user["subscription_status"] == "active"
    assert user["last_payment_date"] == "2025-12-01"

def test_get_user_by_id_not_found(temp_db, monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite:///:memory:")
    db = no_reply_email_system.SQLDataAccess()
    db.conn = temp_db
    user = db.get_user_by_id(999)
    assert user is None

def test_email_log_write_and_read(db_with_log_table):
    cur = db_with_log_table.cursor()
    cur.execute("""INSERT INTO email_log (user_id, email_type, status, error_message, timestamp)
        VALUES (?, ?, ?, ?, ?)""", (1, "welcome", "sent", None, "2025-12-28T12:00:00Z"))
    db_with_log_table.commit()
    cur.execute("SELECT user_id, email_type, status, error_message, timestamp FROM email_log WHERE user_id = ?", (1,))
    row = cur.fetchone()
    assert row[0] == 1
    assert row[1] == "welcome"
    assert row[2] == "sent"
    assert row[3] is None
    assert row[4] == "2025-12-28T12:00:00Z"
