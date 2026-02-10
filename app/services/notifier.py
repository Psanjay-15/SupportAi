# import requests
# from app.config import PUSHOVER_USER, PUSHOVER_TOKEN

# PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

# def send_push_notification(message: str):
#     if not (PUSHOVER_USER and PUSHOVER_TOKEN):
#         print("Pushover credentials missing; skipping notification")
#         return
    
#     print(f"Push: {message}")
#     payload = {"user": PUSHOVER_USER, "token": PUSHOVER_TOKEN, "message": message}
#     try:
#         response = requests.post(PUSHOVER_URL, data=payload)
#         response.raise_for_status()
#     except requests.RequestException as err:
#         print(f"Failed to send Pushover notification: {err}")



import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from app.config import (
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USERNAME,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENT,
    EMAIL_SENDER_NAME,
    EMAIL_FROM,
)

def send_email_notification(
    question: str,
    subject_prefix: str = "Unanswered question from Support AI"
):
    """
    Send email notification when no answer is found (using SMTP).
    Uses credentials from .env (typically Gmail with App Password).
    """
    if not all([EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
        print("Email credentials missing → skipping notification")
        return

    msg = MIMEMultipart()
    msg["From"] = f"{EMAIL_SENDER_NAME} <{EMAIL_FROM or EMAIL_USERNAME}>"
    msg["To"] = EMAIL_RECIPIENT
    msg["Subject"] = f"{subject_prefix}: {question[:70]}…"

    # Email body
    body = f"""
Unanswered question received:

Question:
{question}

Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This is an automated notification from the Support AI system.
Please check if this question should be added to the knowledge base.
    """.strip()

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()  # Enable TLS
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"[EMAIL SENT] Notification sent for question: {question[:50]}…")

    except Exception as e:
        print(f"[EMAIL FAILED] {type(e).__name__}: {str(e)}")