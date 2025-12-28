import pytest
import no_reply_email_system

def test_render_welcome(demo_user):
    html, plain = no_reply_email_system.render_welcome_email(demo_user)
    assert demo_user["name"] in html
    assert "registration" in html.lower()
    assert demo_user["name"] in plain
    assert "registration" in plain.lower()

def test_render_payment_confirmation(demo_user):
    html, plain = no_reply_email_system.render_payment_confirmation_email(demo_user, 10.5, "2025-12-01")
    assert "10.5" in html or "10.50" in html
    assert "2025-12-01" in html
    assert "payment" in html.lower()
    assert "10.5" in plain or "10.50" in plain
    assert "2025-12-01" in plain

def test_render_payment_failed(demo_user):
    html, plain = no_reply_email_system.render_payment_failed_email(demo_user, "2025-12-28")
    assert "not received" in html.lower() or "unable" in html.lower()
    assert "2025-12-28" in html
    assert "not received" in plain.lower() or "unable" in plain.lower()
    assert "2025-12-28" in plain

def test_render_subscription_frozen(demo_user):
    html, plain = no_reply_email_system.render_subscription_frozen_email(demo_user)
    assert "frozen" in html.lower()
    assert "frozen" in plain.lower()
    assert "temporarily" in html.lower()
    assert "temporarily" in plain.lower()
