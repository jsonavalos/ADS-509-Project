
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()  # Loads variables from .env

# For ENV variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email to the given address."""
    msg = MIMEMultipart()
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html")) # can be switched to "html" if needed

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to, msg.as_string())

    print(f"✓ Email sent to {to}")


"""
HOW TO USE.
from mailing_tool import send_email

send_email("user@example.com", "Welcome!", "Thanks for signing up.")
"""