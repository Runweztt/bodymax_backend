"""Pindo SMS service — send alerts to members via https://api.pindo.io"""

import threading
import requests
from config import PINDO_API_TOKEN, PINDO_SENDER

PINDO_URL = "https://api.pindo.io/v1/sms/"


def _send(phone, message):
    """Send a single SMS via Pindo API. Runs in a background thread."""
    if not phone or not PINDO_API_TOKEN:
        return
    # Ensure phone starts with +
    if not phone.startswith("+"):
        phone = f"+{phone}"
    try:
        resp = requests.post(
            PINDO_URL,
            json={"to": phone, "text": message, "sender": PINDO_SENDER},
            headers={"Authorization": f"Bearer {PINDO_API_TOKEN}"},
            timeout=10,
        )
        data = resp.json()
        print(f"[SMS] → {phone}: {data.get('status', 'unknown')} (cost: {data.get('total_cost', '?')})")
    except Exception as e:
        print(f"[SMS] Failed to send to {phone}: {e}")


def send_sms(phone, message):
    """Fire-and-forget SMS — never blocks the request."""
    t = threading.Thread(target=_send, args=(phone, message), daemon=True)
    t.start()


# ── Message Templates ──────────────────────────────────

def welcome_sms(name, phone):
    send_sms(phone, f"Welcome to BodyMax Gym, {name}! 💪 Your membership is now active. See you at the gym!")


def payment_sms(name, phone, amount):
    send_sms(phone, f"Payment of RWF {amount:,} received. Thank you, {name}! Your BodyMax membership is confirmed.")


def checkin_sms(name, phone):
    send_sms(phone, f"Welcome back to BodyMax, {name}! Enjoy your workout 🏋️")


def expiry_sms(name, phone, days):
    if days <= 0:
        send_sms(phone, f"Hi {name}, your BodyMax membership has expired. Renew today to keep training! 💪")
    else:
        send_sms(phone, f"Hi {name}, your BodyMax membership expires in {days} day{'s' if days != 1 else ''}. Renew soon to stay active! 🏋️")
