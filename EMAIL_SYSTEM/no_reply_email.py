import os
import smtplib
import ssl
import time
import logging
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import List, Optional, Union
from html import unescape
import re

# Justification: 'logging' and 'email' are stdlib; no external deps used except for a simple HTML-to-text fallback

def _get_env_var(name: str, required: bool = True, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

# Minimal HTML to plain text fallback
def html_to_text(html: str) -> str:
    # Remove script/style
    html = re.sub(r'<(script|style)[^>]*>.*?</\\1>', '', html, flags=re.DOTALL|re.IGNORECASE)
    # Replace <br> and <p> with newlines
    html = re.sub(r'<br[ \\t\\r\\n]*/*>', '\\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</p[ \\t\\r\\n]*>', '\\n', html, flags=re.IGNORECASE)
    # Remove all other tags
    text = re.sub(r'<[^>]+>', '', html)
    # Unescape HTML entities
    text = unescape(text)
    # Collapse whitespace
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
        self.from_email = os.getenv('FROM_EMAIL', 'no-reply@example.com')
        self.from_name = os.getenv('FROM_NAME', '')
        if not self.from_email:
            raise RuntimeError('FROM_EMAIL must be set')
        if not self.from_email.lower().startswith('no-reply'):
            raise RuntimeError('FROM_EMAIL must be a no-reply address')
        self.logger = logging.getLogger('no_reply_email')
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def send_email(self,
                   to: Union[str, List[str]],
                   subject: str,
                   html_body: str,
                   plain_body: Optional[str] = None,
                   max_retries: int = 3,
                   backoff: float = 2.0) -> None:
        if isinstance(to, str):
            recipients = [to]
        else:
            recipients = list(to)
        if not recipients:
            raise ValueError('At least one recipient required')
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = formataddr((self.from_name, self.from_email)) if self.from_name else self.from_email
        msg['To'] = ', '.join(recipients)
        # No-reply headers
        msg['Reply-To'] = self.from_email
        msg['Auto-Submitted'] = 'auto-generated'
        msg['X-Auto-Response-Suppress'] = 'All'
        msg['Precedence'] = 'bulk'
        msg['Return-Path'] = self.from_email
        msg['Message-ID'] = make_msgid(domain=self.from_email.split('@')[-1])
        # Add more headers if needed to discourage replies
        # Compose body
        if not plain_body:
            plain_body = html_to_text(html_body)
        msg.set_content(plain_body)
        msg.add_alternative(html_body, subtype='html')
        # Send with retries
        attempt = 0
        while True:
            try:
                self._send(msg)
                self.logger.info(f"Email sent to {recipients}")
                break
            except (smtplib.SMTPException, OSError) as e:
                attempt += 1
                self.logger.warning(f"Send attempt {attempt} failed: {e}")
                if attempt >= max_retries:
                    self.logger.error(f"Giving up after {attempt} attempts.")
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

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sender = EmailSender()
    try:
        sender.send_email(
            to=["recipient@example.com"],
            subject="Test No-Reply Email",
            html_body="""
                <html>
                  <body>
                    <h1>Hello!</h1>
                    <p>This is a <b>no-reply</b> transactional email.</p>
                  </body>
                </html>
            """
        )
    except Exception as e:
        print(f"Failed to send email: {e}")
