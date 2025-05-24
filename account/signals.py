# account/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MessageUser
from .tasks import delete_message

@receiver(post_save, sender=MessageUser)
def schedule_delete_message(sender, instance, created, **kwargs):
    if created:
        print(f"✅ Signal ishga tushdi: Xabar ID = {instance.id}")
        delete_message.apply_async((instance.id,), countdown=5*60*60)
        print("✅ Task yuborildi Celery'ga")
