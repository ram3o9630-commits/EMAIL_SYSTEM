import pytest
import email
from unittest import mock
import no_reply_email_system

@pytest.fixture
def sender(smtp_env):
    return no_reply_email_system.EmailSender()

@mock.patch("smtplib.SMTP")
def test_headers_and_mime(mock_smtp, sender, demo_user):
    instance = mock_smtp.return_value.__enter__.return_value
    sent_msgs = []
    instance.send_message.side_effect = lambda msg: sent_msgs.append(msg)
    sender.send_email(
        to=[demo_user["email"]],
        subject="Test Subject",
        html_body="<b>Hello</b>",
        plain_body="Hello"
    )
    assert sent_msgs, "No email sent"
    msg = sent_msgs[0]
    assert msg["From"] == sender.from_email or sender.from_email in msg["From"]
    assert msg["To"] == demo_user["email"]
    assert msg["Subject"] == "Test Subject"
    assert msg["Reply-To"] == sender.from_email
    assert msg["Auto-Submitted"] == "auto-generated"
    assert msg["X-Auto-Response-Suppress"] == "All"
    assert msg["Precedence"] == "bulk"
    assert msg["Return-Path"] == sender.from_email
    assert msg["Message-ID"]
    assert msg.get_content_type() == "multipart/alternative"
    parts = {p.get_content_type(): p for p in msg.iter_parts()}
    assert "text/plain" in parts
    assert "text/html" in parts
    assert "Hello" in parts["text/plain"].get_content()
    assert "<b>Hello</b>" in parts["text/html"].get_content()
