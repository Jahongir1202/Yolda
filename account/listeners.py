# listeners.py
from telethon import TelegramClient, events
from .models import MessageUser as DBMessage

from channels.layers import get_channel_layer
from telethon.events import NewMessage
import asyncio
from django.core.cache import cache

from account.models import TelegramAccount

channel_layer = get_channel_layer()
api_id = 28642576
api_hash = "a61168101688d1d20e70214087fb037a"

async def listen(account):
    print(f"👂 Tinglash boshlandi: {account.phone_number}")
    client = TelegramClient(f"{account.phone_number}", api_id, api_hash)

    try:
        await client.start()
        print(f"✅ Client ishga tushdi: {account.phone_number}")
    except Exception as e:
        print(f"❌ Clientni ishga tushirishda xatolik: {e}")
        return

    @client.on(NewMessage)
    async def handler(event):
        message = event.message.message
        print(f"🔔 Yangi xabar kelgan: {message}")
        digit_count = sum(c.isdigit() for c in message)
        if digit_count < 9:
            print("⚠️ Xabar rad etildi – raqamlar soni 9 dan kam.")
            return  # Bazaga yozmasdan chiqamiz

        # DBga saqlash
        from asgiref.sync import sync_to_async
        msg = await sync_to_async(DBMessage.objects.create)(text=message)

        await channel_layer.group_send(
            "chat_group",
            {
                "type": "chat_message",
                "message": message,
                "id": msg.id
            }
        )

        cache.set("last_message", message)

    await client.run_until_disconnected()

def start_listening():
    accounts = TelegramAccount.objects.filter(is_default=True)
    if not accounts:
        print("❗ Hisob topilmadi!")
        return

    loop = asyncio.get_event_loop()

    for account in accounts:
        loop.create_task(listen(account))

    print("🚀 Barcha accountlar uchun tinglash boshlandi...")
    loop.run_forever()
