# services.py
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import UserBannedInChannelError, ChatWriteForbiddenError
import asyncio
import logging


API_HASH = "a61168101688d1d20e70214087fb037a"
API_ID = 28642576


async def connect_client(session_name):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()
    return client




import asyncio
from telethon.errors import UserBannedInChannelError, ChatWriteForbiddenError
async def send_to_all_groups(session_name, message, last_index=0, batch_size=10):
    client = await connect_client(session_name)
    if not await client.is_user_authorized():
        await client.disconnect()
        print("❌ Avtorizatsiyadan o'tmagan")
        return last_index

    dialogs = await client.get_dialogs(limit=None)
    groups = [
        d for d in dialogs
        if (d.is_group or getattr(d.entity, 'megagroup', False))
    ]

    if not groups:
        print("⚠️ Guruhlar topilmadi")
        await client.disconnect()
        return last_index

    print(f"📊 {len(groups)} ta guruh topildi. Boshlanish index: {last_index}")

    current_index = last_index
    sent = 0
    batch_sent = 0

    while batch_sent < batch_size and current_index < len(groups):
        group = groups[current_index]
        print(f"➡️ [{sent + 1}] Guruh: {group.name} (ID: {group.id})")
        try:
            await client.send_message(group.id, message)
            print(f"✅ Yuborildi: {group.name}")
            sent += 1
            batch_sent += 1
        except (UserBannedInChannelError, ChatWriteForbiddenError):
            print(f"🚫 Ruxsat yo'q yoki ban: {group.name}")
        except Exception as e:
            print(f"❌ Xatolik: {group.name} - {e}")
        current_index += 1

    await client.disconnect()
    print("✅ Batch yakunlandi")
    return current_index  # qaytgan index keyingi guruhdan davom etadi

def send_to_all_groups_sync(session_name, message, last_index=0):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            send_to_all_groups(session_name, message, last_index)
        )
    except Exception as e:
        print(f"⚠️ Umumiy xatolik: {e}")
        return last_index

