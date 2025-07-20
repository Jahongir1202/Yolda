from django.test import TestCase, Client
from unittest.mock import patch
from django.urls import reverse
from account.models import MessageCooldown

class SendToGroupsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("send_to_groups", args=[1])
        MessageCooldown.objects.create(id=1, last_sent_time=0)

    @patch("account.services.send_to_all_groups_sync")
    def test_send_to_groups_post_success(self, mock_send):
        mock_send.return_value = 12345  # Fake message ID returned from service

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"success": True, "message_id": 12345}
        )
        mock_send.assert_called_once_with(1)

    def test_send_to_groups_method_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"success": False, "error": "Only POST method is allowed"}
        )
