import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import transaction
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

from .models import MessageUser, User


class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chat_group"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'take':
            message_id = data.get('id')

            # Session orqali user_id ni olish va User modelidan userni topish
            user = await self.get_user_from_session()

            if user:
                success = await self.try_take_message(message_id, user)

                if success:
                    # boshqa clientlarga xabarni delete qilish haqida yuborish
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_delete',
                            'id': message_id,
                            'exclude_channel': self.channel_name
                        }
                    )

                    # Xabarni olgan foydalanuvchiga uni o‘zining xabarlar bo‘limiga olish uchun yuborish
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_taken',
                            'id': message_id,
                            'taken_by': user.username
                        }
                    )
            else:
                print("Foydalanuvchi topilmadi yoki login qilinmagan.")

        elif action == 'send':
            message = data.get('message')
            msg_id, msg_text = await self.save_message(message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': msg_text,
                    'id': msg_id
                }
            )

    # 🔹 Xabarni saqlovchi funksiya
    @sync_to_async
    def save_message(self, message):
        msg = MessageUser.objects.create(text=message)
        return msg.id, msg.text

    # 🔹 Foydalanuvchini sessiondan olish
    @database_sync_to_async
    def get_user_from_session(self):
        session = self.scope.get("session")
        user_id = session.get("user_id")

        if user_id:
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None
        return None

    # 🔹 Xabarni olish funksiyasi
    @database_sync_to_async
    def try_take_message(self, message_id, user):
        try:
            with transaction.atomic():
                msg = MessageUser.objects.select_for_update().get(id=message_id)
                if msg.taken_by is None:
                    msg.taken_by = user
                    msg.save()
                    return True
        except MessageUser.DoesNotExist:
            return False
        return False

    # 🔹 Yangi xabarni yuborish
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'id': event['id'],
            'taken_by': None
        }))

    # 🔹 Xabarni o‘chirish (agar olinsa)
    async def chat_delete(self, event):
        if self.channel_name != event['exclude_channel']:
            await self.send(text_data=json.dumps({
                'type': 'delete',
                'id': event['id']
            }))

    # 🔹 Xabarni olingan deb belgilash
    async def chat_taken(self, event):
        await self.send(text_data=json.dumps({
            'type': 'taken',
            'id': event['id'],
            'taken_by': event['taken_by']
        }))
