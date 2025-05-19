from django.core.management.base import BaseCommand
from account.listeners import start_listening  # start_listening funksiyasini import qilamiz

class Command(BaseCommand):
    help = 'Telegram guruhlari uchun xabarlarni tinglashni boshlash'

    def handle(self, *args, **kwargs):
        start_listening()  # Tinglashni boshlash
