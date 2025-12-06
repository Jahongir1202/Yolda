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
from django.utils import timezone
from account.services import send_to_all_groups_sync

API_ID = 28642576
API_HASH = "a61168101688d1d20e70214087fb037a"



class TelegramAccount(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    session_name = models.CharField(max_length=255, unique=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    last_group_index = models.IntegerField(default=0)
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
                qr_url = qr_login.url  # Faqat URL qismi olinadi

                import qrcode
                from io import BytesIO
                from django.core.files.base import ContentFile

                qr_img = qrcode.make(qr_url)
                buffer = BytesIO()
                qr_img.save(buffer, format="PNG")
                buffer.seek(0)

                file_name = f'{self.session_name}_qr.png'
                self.qr_code.save(file_name, ContentFile(buffer.read()), save=False)

            await client.disconnect()

        loop.run_until_complete(generate_qr())
        super().save(*args, **kwargs)



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
            sent = send_to_all_groups_sync(account.session_name, self.text)
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
    session_token = models.CharField(max_length=255, blank=True, null=True)
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

class ArxivMessage(models.Model):
    qayerda = models.CharField(max_length=100)
    qayerga = models.CharField(max_length=100)
    cars = models.CharField(max_length=100)
    text = models.CharField(max_length=500)
    narxi = models.CharField(max_length=100)

    def __str__(self):
        return self.cars


class MessageCooldown(models.Model):
    last_sent_at = models.DateTimeField(default=timezone.now)

    def is_allowed(self):
        now = timezone.now()
        delta = now - self.last_sent_at
        return delta.total_seconds() >= 120

class ApiMessage(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:40]