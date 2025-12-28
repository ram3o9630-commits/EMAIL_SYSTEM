import pytest
from unittest import mock
import no_reply_email_system

@pytest.fixture
def sender(smtp_env):
    return no_reply_email_system.EmailSender()

@mock.patch("smtplib.SMTP")
def test_send_welcome_email(mock_smtp, sender, demo_user):
    instance = mock_smtp.return_value.__enter__.return_value
    sent_msgs = []
    instance.send_message.side_effect = lambda msg: sent_msgs.append(msg)
    no_reply_email_system.send_welcome_email(sender, demo_user)
    assert sent_msgs, "No email sent"
    msg = sent_msgs[0]
    assert "Welcome" in msg["Subject"]

@mock.patch("smtplib.SMTP")
def test_send_payment_confirmation_email(mock_smtp, sender, demo_user):
    instance = mock_smtp.return_value.__enter__.return_value
    sent_msgs = []
    instance.send_message.side_effect = lambda msg: sent_msgs.append(msg)
    no_reply_email_system.send_payment_confirmation_email(sender, demo_user, 10.5, "2025-12-01")
    assert sent_msgs, "No email sent"
    msg = sent_msgs[0]
    assert "Payment Confirmation" in msg["Subject"]

@mock.patch("smtplib.SMTP")
def test_send_payment_failed_email(mock_smtp, sender, demo_user):
    instance = mock_smtp.return_value.__enter__.return_value
    sent_msgs = []
    instance.send_message.side_effect = lambda msg: sent_msgs.append(msg)
    no_reply_email_system.send_payment_failed_email(sender, demo_user, "2025-12-28")
    assert sent_msgs, "No email sent"
    msg = sent_msgs[0]
    assert "Payment Not Received" in msg["Subject"]

@mock.patch("smtplib.SMTP")
def test_send_subscription_frozen_email(mock_smtp, sender, demo_user):
    instance = mock_smtp.return_value.__enter__.return_value
    sent_msgs = []
    instance.send_message.side_effect = lambda msg: sent_msgs.append(msg)
    no_reply_email_system.send_subscription_frozen_email(sender, demo_user)
    assert sent_msgs, "No email sent"
    msg = sent_msgs[0]
    assert "Subscription Frozen" in msg["Subject"]
