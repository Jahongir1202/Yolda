# services.py
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import UserBannedInChannelError, ChatWriteForbiddenError
import asyncio

API_ID = 28642576
API_HASH = "a61168101688d1d20e70214087fb037a"


async def connect_client(session_name):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()
    return client


async def send_message(session_name, group_id, message):
    client = await connect_client(session_name)

    if await client.is_user_authorized():
        try:
            await client.send_message(group_id, message)
        finally:
            await client.disconnect()
        return True

    await client.disconnect()
    return False


def send_message_to_group(session_name, group_id, message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(send_message(session_name, group_id, message))


async def send_to_all(session_name, message):
    client = await connect_client(session_name)
    if not await client.is_user_authorized():
        await client.disconnect()
        return False

    dialogs = await client.get_dialogs()
    failed_groups = []

    for dialog in dialogs:
        if dialog.is_group and not dialog.is_channel:
            try:
                await client.send_message(dialog.entity.id, message)
                print(f"✅ Yuborildi: {dialog.name}")
            except Exception as e:
                print(f"❌ {dialog.name} - {e}")
                failed_groups.append(dialog.name)

    await client.disconnect()

    if failed_groups:
        print("⚠️ Quyidagi guruhlarga yuborilmadi:", ", ".join(failed_groups))
        return False
    return True


def send_to_all_groups(session_name, message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(send_to_all(session_name, message))


async def send_to_10_groups(session_name, message, last_index):
    client = await connect_client(session_name)
    if not await client.is_user_authorized():
        await client.disconnect()
        print("❌ Avtorizatsiyadan o'tmagan")
        return last_index

    dialogs = await client.get_dialogs()
    groups = [d for d in dialogs if d.is_group and not d.is_channel]

    if not groups:
        print("⚠️ Guruhlar yo'q")
        await client.disconnect()
        return last_index

    print(f"📊 {len(groups)} ta guruh topildi")

    sent, new_index, attempts = 0, last_index, 0
    while sent < 10 and attempts < len(groups):
        group = groups[new_index % len(groups)]
        try:
            await client.send_message(group.id, message)
            print(f"✅ Yuborildi: {group.name}")
            sent += 1
        except (UserBannedInChannelError, ChatWriteForbiddenError) as e:
            print(f"🚫 Ruxsat yo'q yoki ban: {group.name}")
        except Exception as e:
            print(f"❌ Xatolik: {group.name} - {e}")
        new_index += 1
        attempts += 1

    await client.disconnect()
    return new_index % len(groups)


def send_to_10_groups_sync(session_name, message, last_index):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(send_to_10_groups(session_name, message, last_index))
    except Exception as e:
        print(f"⚠️ Umumiy xatolik: {e}")
        return last_index
