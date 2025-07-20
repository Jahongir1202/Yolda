from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from unittest.mock import patch
from account.models import User, ArxivMessage, TelegramAccount, MessageCooldown
import threading
import time

class SendMessageViewTest(TestCase):
    def setUp(self):
        cache.delete('telegram_send_lock')

        self.user1 = User.objects.create(username='user1', password='123')
        self.user2 = User.objects.create(username='user2', password='123')

        self.message = ArxivMessage.objects.create(
            qayerda="Toshkent",
            qayerga="Andijon",
            cars="Malibu",
            text="Yuk bor",
            narxi="1 mln"
        )

        TelegramAccount.objects.create(
            phone_number="+998901234567",
            session_name="testsession",
            is_logged_in=True,
            is_default=True
        )

        MessageCooldown.objects.create(id=1)

        self.client1 = Client()
        self.client2 = Client()
        self.login_user(self.client1, self.user1)
        self.login_user(self.client2, self.user2)

    def login_user(self, client, user):
        session = client.session
        session['user_id'] = user.id
        session['session_token'] = "fake-token"
        session.save()

    @patch("account.services.send_to_all_groups_sync", return_value=999)
    def test_send_message_with_lock(self, mock_send):
        """🔐 Bir vaqtning o'zida 2ta dispecher yuborishga urinsa — faqat 1tasi yuboradi"""

        responses = [None, None]

        def send(client, index):
            res = client.post(reverse('send_to_groups', args=[self.message.id]))
            responses[index] = res

        t1 = threading.Thread(target=send, args=(self.client1, 0))
        t2 = threading.Thread(target=send, args=(self.client2, 1))

        t1.start()
        time.sleep(0.1)  # lock olish uchun ustunlik beradi
        t2.start()
        t1.join()
        t2.join()

        success = 0
        locked = 0

        for res in responses:
            messages = res.wsgi_request._messages._queued_messages
            if any("❌ Boshqa dispecher" in str(m.message) for m in messages):
                locked += 1
            else:
                success += 1

        self.assertEqual(success, 1)
        self.assertEqual(locked, 1)
        print("✅ Redis lock to'g'ri ishladi: faqat 1 ta yuborildi")

    @patch("account.services.send_to_all_groups_sync", return_value=100)
    def test_send_message_success(self, mock_send):
        """✅ Oddiy yuborish test — hech kim bloklamayapti"""
        response = self.client1.post(reverse('send_to_groups', args=[self.message.id]))
        self.assertEqual(response.status_code, 302)
        mock_send.assert_called_once()
        print("✅ Yuborish muvaffaqiyatli bo'ldi")
