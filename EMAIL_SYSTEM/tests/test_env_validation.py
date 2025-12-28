import pytest
import no_reply_email_system

def test_missing_smtp_host(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("FROM_EMAIL", "no-reply@test.local")
    with pytest.raises(Exception) as e:
        no_reply_email_system.EmailSender()
    assert "SMTP_HOST" in str(e.value)

def test_missing_smtp_port(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.delenv("SMTP_PORT", raising=False)
    monkeypatch.setenv("FROM_EMAIL", "no-reply@test.local")
    with pytest.raises(Exception) as e:
        no_reply_email_system.EmailSender()
    assert "SMTP_PORT" in str(e.value)

def test_missing_from_email(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("DB_URL", "sqlite:///:memory:")
    monkeypatch.delenv("FROM_EMAIL", raising=False)
    with pytest.raises(RuntimeError) as e:
        no_reply_email_system.EmailSender()
    assert "FROM_EMAIL" in str(e.value)

def test_from_email_not_no_reply(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("FROM_EMAIL", "user@test.local")
    with pytest.raises(Exception) as e:
        no_reply_email_system.EmailSender()
    assert "no-reply" in str(e.value)
