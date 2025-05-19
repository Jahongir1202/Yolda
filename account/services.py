# services.py
from telethon import TelegramClient
import asyncio

API_ID = 28642576
API_HASH = "a61168101688d1d20e70214087fb037a"


async def send_message(session_name, group_id, message):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()

    if await client.is_user_authorized():
        await client.send_message(group_id, message)
        await client.disconnect()
        return True

    await client.disconnect()
    return False


def send_message_to_group(session_name, group_id, message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(send_message(session_name, group_id, message))


async def send_to_all(session_name, message):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()  # client.start() o'rniga client.connect() ishlating

    dialogs = await client.get_dialogs()
    success = True
    failed_groups = []  # Yuborilmagan guruhlar ro'yxati

    for dialog in dialogs:
        if dialog.is_group and not dialog.is_channel:
            try:
                await client.send_message(dialog.entity.id, message)
                print(f"Xabar yuborildi: {dialog.name}")
            except Exception as e:
                print(f"Guruhga yuborishda xatolik: {dialog.name} - {e}")
                failed_groups.append(dialog.name)  # Qaysi guruhlar muvaffaqiyatsiz yuborilganligini saqlash
                success = False

    await client.disconnect()

    if failed_groups:
        print(f"Xatolik yuz berdi, quyidagi guruhlarga xabar yuborilmadi: {', '.join(failed_groups)}")

    return success


def send_to_all_groups(session_name, message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(send_to_all(session_name, message))
