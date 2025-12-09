import requests
from django.conf import settings

def send_telegram_message(text: str):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHANNEL_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram error:", e)
