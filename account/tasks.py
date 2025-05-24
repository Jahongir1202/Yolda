from celery import shared_task
from .models import MessageUser

@shared_task
def delete_message(message_id):
    print(f"🔔 Task ishga tushdi. Xabar ID: {message_id}")
    try:
        msg = MessageUser.objects.get(id=message_id)
        msg.delete()
        print(f"✅ Xabar (ID: {message_id}) o'chirildi.")
    except MessageUser.DoesNotExist:
        print(f"❌ Xabar (ID: {message_id}) topilmadi.")
