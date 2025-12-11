import smtplib
import os
from email.message import EmailMessage

def send_email(notification):
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = notification.email
    msg["Subject"] = notification.subject
    msg.set_content(notification.text)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            #server.starttls()
            #server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False