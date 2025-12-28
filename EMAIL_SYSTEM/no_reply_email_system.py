import os
import smtplib
import ssl
import time
import logging
import sqlite3  # Use sqlite3 for demo; code is compatible with PostgreSQL/MySQL via DB-API 2.0
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import List, Optional, Dict, Any, Tuple
from html import unescape
import re

# --- CONFIGURATION ---
def _get_env_var(name: str, required: bool = True, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

# --- LOGGING ---
logger = logging.getLogger('no_reply_email_system')
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# --- EMAIL SENDER ---
def html_to_text(html: str) -> str:
    html = re.sub(r'<(script|style)[^>]*>.*?</\\1>', '', html, flags=re.DOTALL|re.IGNORECASE)
    html = re.sub(r'<br[ \\t\\r\\n]*/*>', '\\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p[ \\t\\r\\n]*>', '\\n', html, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', html)
    text = unescape(text)
    text = re.sub(r'\\s+', ' ', text)
    return text.strip()

class EmailSender:
    def __init__(self):
        self.smtp_host = _get_env_var('SMTP_HOST')
        self.smtp_port = int(_get_env_var('SMTP_PORT'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.use_tls = os.getenv('SMTP_USE_TLS', 'false').lower() == 'true'
        self.use_ssl = os.getenv('SMTP_USE_SSL', 'false').lower() == 'true'
        self.from_email = os.getenv('FROM_EMAIL')
        self.from_name = os.getenv('FROM_NAME', '')
        if not self.from_email:
            raise RuntimeError('FROM_EMAIL must be set')
        if not self.from_email.lower().startswith('no-reply'):
            raise RuntimeError('FROM_EMAIL must be a no-reply address')

    def send_email(self,
                   to: List[str],
                   subject: str,
                   html_body: str,
                   plain_body: Optional[str] = None,
                   max_retries: int = 3,
                   backoff: float = 2.0) -> None:
        if not to:
            raise ValueError('At least one recipient required')
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = formataddr((self.from_name, self.from_email)) if self.from_name else self.from_email
        msg['To'] = ', '.join(to)
        msg['Reply-To'] = self.from_email
        msg['Auto-Submitted'] = 'auto-generated'
        msg['X-Auto-Response-Suppress'] = 'All'
        msg['Precedence'] = 'bulk'
        msg['Return-Path'] = self.from_email
        msg['Message-ID'] = make_msgid(domain=self.from_email.split('@')[-1])
        if not plain_body:
            plain_body = html_to_text(html_body)
        msg.set_content(plain_body)
        msg.add_alternative(html_body, subtype='html')
        attempt = 0
        while True:
            try:
                self._send(msg)
                logger.info(f"Email sent to {to}")
                break
            except (smtplib.SMTPException, OSError) as e:
                attempt += 1
                logger.warning(f"Send attempt {attempt} failed: {e}")
                if attempt >= max_retries:
                    logger.error(f"Giving up after {attempt} attempts.")
                    raise
                time.sleep(backoff * attempt)

    def _send(self, msg: EmailMessage) -> None:
        if self.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                self._login(server)
                server.send_message(msg)
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                self._login(server)
                server.send_message(msg)

    def _login(self, server):
        if self.smtp_username and self.smtp_password:
            server.login(self.smtp_username, self.smtp_password)

# --- SQL DATA ACCESS ---
class SQLDataAccess:
    def __init__(self):
        self.db_url = _get_env_var('DB_URL')
        self.conn = self._connect()

    def _connect(self):
        # For SQLite: DB_URL=sqlite:///path/to/file.db or :memory:
        if self.db_url.startswith('sqlite:///'):
            path = self.db_url.replace('sqlite:///', '', 1)
            return sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        elif self.db_url == 'sqlite://:memory:':
            return sqlite3.connect(':memory:')
        else:
            raise NotImplementedError('Only SQLite is implemented in this example. Use DB-API 2.0 for other engines.')

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, email, name, subscription_status, last_payment_date FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'subscription_status': row[3],
                'last_payment_date': row[4],
            }
        return None

    def close(self):
        self.conn.close()

# --- EMAIL TEMPLATES ---
def render_welcome_email(user: Dict[str, Any]) -> Tuple[str, str]:
    html = f"""
    <html><body>
    <h2>Welcome, {user['name']}!</h2>
    <p>Your registration was successful. Your account is now active and you have full access to our platform.</p>
    <p>If you have any questions, please contact our support team.</p>
    <p>Best regards,<br>The Team</p>
    </body></html>
    """
    plain = f"""
    Welcome, {user['name']}!

    Your registration was successful. Your account is now active and you have full access to our platform.

    If you have any questions, please contact our support team.

    Best regards,
    The Team
    """
    return html, plain

def render_payment_confirmation_email(user: Dict[str, Any], amount: float, payment_date: str) -> Tuple[str, str]:
    html = f"""
    <html><body>
    <h2>Payment Received</h2>
    <p>Dear {user['name']},</p>
    <p>We have received your payment of <b>${amount:.2f}</b> on {payment_date}.</p>
    <p>Your subscription remains active. Thank you for your continued trust.</p>
    <p>Best regards,<br>The Team</p>
    </body></html>
    """
    plain = f"""
    Payment Received

    Dear {user['name']},

    We have received your payment of ${amount:.2f} on {payment_date}.

    Your subscription remains active. Thank you for your continued trust.

    Best regards,
    The Team
    """
    return html, plain

def render_payment_failed_email(user: Dict[str, Any], due_date: str) -> Tuple[str, str]:
    html = f"""
    <html><body>
    <h2>Payment Not Received</h2>
    <p>Dear {user['name']},</p>
    <p>We were unable to process your recent payment due on {due_date}.</p>
    <p>Please check your payment method. If unresolved, your service may be impacted.</p>
    <p>To avoid interruption, please update your payment information at your earliest convenience.</p>
    <p>Best regards,<br>The Team</p>
    </body></html>
    """
    plain = f"""
    Payment Not Received

    Dear {user['name']},

    We were unable to process your recent payment due on {due_date}.

    Please check your payment method. If unresolved, your service may be impacted.

    To avoid interruption, please update your payment information at your earliest convenience.

    Best regards,
    The Team
    """
    return html, plain

def render_subscription_frozen_email(user: Dict[str, Any]) -> Tuple[str, str]:
    html = f"""
    <html><body>
    <h2>Subscription Frozen</h2>
    <p>Dear {user['name']},</p>
    <p>Your subscription has been temporarily frozen due to unresolved payment issues.</p>
    <p>Some platform features are currently limited. Once payment is resolved, your subscription will be fully reactivated.</p>
    <p>If you need assistance, please contact support.</p>
    <p>Best regards,<br>The Team</p>
    </body></html>
    """
    plain = f"""
    Subscription Frozen

    Dear {user['name']},

    Your subscription has been temporarily frozen due to unresolved payment issues.

    Some platform features are currently limited. Once payment is resolved, your subscription will be fully reactivated.

    If you need assistance, please contact support.

    Best regards,
    The Team
    """
    return html, plain

# --- EVENT-TRIGGERED EMAIL FUNCTIONS ---
def send_welcome_email(email_sender: EmailSender, user: Dict[str, Any]):
    html, plain = render_welcome_email(user)
    email_sender.send_email(
        to=[user['email']],
        subject="Welcome to Our Platform",
        html_body=html,
        plain_body=plain
    )

def send_payment_confirmation_email(email_sender: EmailSender, user: Dict[str, Any], amount: float, payment_date: str):
    html, plain = render_payment_confirmation_email(user, amount, payment_date)
    email_sender.send_email(
        to=[user['email']],
        subject="Payment Confirmation",
        html_body=html,
        plain_body=plain
    )

def send_payment_failed_email(email_sender: EmailSender, user: Dict[str, Any], due_date: str):
    html, plain = render_payment_failed_email(user, due_date)
    email_sender.send_email(
        to=[user['email']],
        subject="Payment Not Received",
        html_body=html,
        plain_body=plain
    )

def send_subscription_frozen_email(email_sender: EmailSender, user: Dict[str, Any]):
    html, plain = render_subscription_frozen_email(user)
    email_sender.send_email(
        to=[user['email']],
        subject="Subscription Frozen",
        html_body=html,
        plain_body=plain
    )

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # For demo: create a test SQLite DB in memory
    os.environ['DB_URL'] = 'sqlite:///:memory:'
    db = SQLDataAccess()
    cur = db.conn.cursor()
    cur.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL,
        name TEXT NOT NULL,
        subscription_status TEXT,
        last_payment_date TEXT
    )''')
    cur.execute('''INSERT INTO users (id, email, name, subscription_status, last_payment_date) VALUES (?, ?, ?, ?, ?)''',
                (1, 'customer@example.com', 'Jane Doe', 'active', '2025-12-01'))
    db.conn.commit()
    user = db.get_user_by_id(1)
    # Set up SMTP env vars for demo (replace with real values in production)
    os.environ['SMTP_HOST'] = 'smtp.example.com'
    os.environ['SMTP_PORT'] = '587'
    os.environ['FROM_EMAIL'] = 'no-reply@example.com'
    os.environ['SMTP_USE_TLS'] = 'true'
    # os.environ['SMTP_USERNAME'] = 'your_username'
    # os.environ['SMTP_PASSWORD'] = 'your_password'
    sender = EmailSender()
    try:
        send_welcome_email(sender, user)
        send_payment_confirmation_email(sender, user, amount=49.99, payment_date='2025-12-01')
        send_payment_failed_email(sender, user, due_date='2025-12-28')
        send_subscription_frozen_email(sender, user)
    except Exception as e:
        print(f"Failed to send email: {e}")
    db.close()
