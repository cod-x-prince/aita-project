# FILE: utils/notifications.py
import smtplib
import os
from email.message import EmailMessage
import requests
from dotenv import load_dotenv

def send_email(subject, body):
    """Sends an email using credentials from the .env file."""
    
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")
    
    if not all([sender, password, receiver]):
        print("Email credentials not found in .env file. Skipping email.")
        return

    # Create the email message
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("Email report sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_mobile_alert(event_name, symbol, pnl, exit_reason):
    """Sends a real-time mobile alert with detailed trade info via IFTTT."""
    key = os.getenv("IFTTT_WEBHOOK_KEY")
    if not key:
        print("IFTTT key not found in .env file. Skipping mobile alert.")
        return

    url = f"httpshttps://maker.ifttt.com/trigger/{event_name}/with/key/{key}"
    
    # Determine the outcome text
    outcome = "PROFIT" if pnl > 0 else "LOSS"
    
    # Create the data payload with three values
    payload = {
        'value1': symbol,
        'value2': f"{outcome} of Rs. {pnl:,.2f}",
        'value3': exit_reason
    }

    try:
        requests.post(url, json=payload)
        print("Detailed mobile alert sent successfully.")
    except Exception as e:
        print(f"Failed to send mobile alert: {e}")