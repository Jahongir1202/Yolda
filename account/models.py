# models.py
from sqlite3 import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User
import asyncio
from io import BytesIO
from django.db import models
from django.core.files.base import ContentFile
from telethon import TelegramClient
import qrcode

from account.services import  send_to_all_groups

API_ID = 28642576
API_HASH = "a61168101688d1d20e70214087fb037a"



class TelegramAccount(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    session_name = models.CharField(max_length=255, unique=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    is_logged_in = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.phone_number

    def save(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def generate_qr():
            client = TelegramClient(self.session_name, API_ID, API_HASH)
            await client.connect()

            if not await client.is_user_authorized():
                qr_login = await client.qr_login()
                qr_data = qr_login.url

                qr = qrcode.make(qr_data)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                self.qr_code.save(f'{self.session_name}_qr.png', ContentFile(buffer.getvalue()), save=False)

            await client.disconnect()

        loop.run_until_complete(generate_qr())
        super().save(*args, **kwargs)

    async def async_send_message_to_groups(self, message_text):
        client = TelegramClient(self.session_name, API_ID, API_HASH)
        await client.start()

        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                await client.send_message(dialog.id, message_text)

        await client.disconnect()

    def send_message_to_groups(self, message_text):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.async_send_message_to_groups(message_text))

class Message(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('sent', 'Yuborildi'),
        ('failed', 'Xatolik'),
    ]

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        success = True

        for account in TelegramAccount.objects.filter(is_logged_in=True):
            sent = send_to_all_groups(account.session_name, self.text)
            if not sent:
                success = False

        self.status = 'sent' if success else 'failed'
        super().save(update_fields=['status'])
# models.py
class TelegramGroup(models.Model):
    title = models.CharField(max_length=255)
    group_id = models.BigIntegerField(unique=True)
    account = models.ForeignKey(TelegramAccount, on_delete=models.CASCADE, related_name='groups')

    def __str__(self):
        return f"{self.title} ({self.group_id})"

from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

class MessageUser(models.Model):
    text = models.TextField()
    taken_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    def take_message(self, user):
        try:
            # Foydalanuvchi mavjudligini tekshirish
            taken_by_user = User.objects.get(id=user.id)
            self.taken_by = taken_by_user
            self.save()
        except ObjectDoesNotExist:
            raise IntegrityError("Foydalanuvchi mavjud emas!")

