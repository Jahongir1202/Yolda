from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import  send_to_all_groups_sync
from .models import User, MessageUser, TelegramAccount, Message, ArxivMessage
import json
import logging
import time
from .models import MessageCooldown
from django.utils import timezone
from datetime import timedelta
logger = logging.getLogger('views')

@csrf_exempt
def show_last_message(request):
    logger.info("calling show_last_message()")
    if request.method == 'POST':
        qayerda = request.POST.get('qayerda')
        qayerga = request.POST.get('qayerga')
        cars = request.POST.get('cars')
        text = request.POST.get('text')
        narxi = request.POST.get('narxi')

        if all([qayerda, qayerga, cars, text, narxi]):
            arxiv = ArxivMessage.objects.create(
                qayerda=qayerda,
                qayerga=qayerga,
                cars=cars,
                text=text,
                narxi=narxi
            )

            message = (
                f"Qayerda: {qayerda}\n"
                f"Qayerga: {qayerga}\n"
                f"Avtomobil: {cars}\n"
                f"Matn: {text}\n"
                f"Narxi: {narxi}"
            )


        return send_to_groups(request, msg_id=arxiv.id)

    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    messages = MessageUser.objects.filter(
        taken_by__isnull=True
    ) | MessageUser.objects.filter(taken_by__id=user_id)

    return render(request, 'list.html', {
        'messages': messages.order_by('-created_at'),
        'user_id': user_id
    })



@csrf_exempt
def send_to_groups(request, msg_id):
    logger.info("Calling send_to_groups()")
    cooldown, _ = MessageCooldown.objects.get_or_create(id=1)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST so‘rov kerak'}, status=405)
    if not cooldown.is_allowed():
        remaining = 120 - int((timezone.now() - cooldown.last_sent_at).total_seconds())
        return JsonResponse({'success': False, 'error': f'{remaining} soniyadan keyin yuboring.'}, status=429)

    try:
        arxiv_msg = ArxivMessage.objects.get(id=msg_id)

        base_message = (
            f"Yo'nalish: {arxiv_msg.qayerda} ----> {arxiv_msg.qayerga}\n"
            f"\n"
            f"Avtomobil: {arxiv_msg.cars}\n"
            f"\n"
            f"Matn: {arxiv_msg.text}\n"
            f"\n"
            f"Narxi: {arxiv_msg.narxi}\n"
            f"\n"
            f"\n"
            f"\n"
            f"----------------Yoldauz --------------\n"
        )

        title_variants = [
            "‼️ E'lon: Ahmiyatli yuk",
            "📌 Yuk uchun yangi marshrut",
            "🚛 Yuk borligi haqida xabar",
            "📦 Tezkor yuk yetkazish e'loni",
            "🔔 Diqqat! Yangi yuk bor"
        ]

        batch_size = 10
        delay_seconds = 5

        accounts = TelegramAccount.objects.filter(is_default=True)

        for account in accounts:
            print(f"📨 Yuborish boshlandi: {account.session_name}")

            index = 0
            title_index = 0

            while True:
                # Sarlavha har safar yangilanadi
                title = title_variants[title_index % len(title_variants)]
                title_index += 1

                message = f"{title}\n\n{base_message}"

                # Faqat 10 taga yuboriladi
                result_index = send_to_all_groups_sync(
                    session_name=account.session_name,
                    message=message,
                    last_index=index,
                )

                if result_index == 0 or result_index <= index:
                    print("✅ Barcha guruhlarga yuborish tugadi")
                    break

                index = result_index
                print(f"✅ {batch_size} ta yuborildi. Keyingi: {index}")
                time.sleep(delay_seconds)

            account.last_group_index = 0
            account.save()
            print(f"📥 Yuborish tugadi: {account.session_name}")
            cooldown.last_sent_at = timezone.now()
            cooldown.save()
        return redirect('show_last_message')

    except ArxivMessage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Xabar topilmadi'}, status=404)
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        return JsonResponse({'success': True})



def my_messages_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    my_messages = MessageUser.objects.filter(taken_by_id=user_id).order_by('-created_at')
    return render(request, 'my_list.html', {'messages': my_messages})
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username, password=password)

            # ❌ Agar token allaqachon mavjud bo‘lsa, boshqa qurilmadan login qilishga ruxsat berilmaydi
            if user.session_token:
                messages.error(request, "Bu hisob boshqa qurilmada allaqachon tizimga kirgan!")
                return render(request, 'login.html')

            # ✅ Yangi token yaratamiz (oddiy misol: user ID + IP address)
            import uuid
            token = str(uuid.uuid4())
            user.session_token = token
            user.save()

            # 🔐 Tokenni session'ga yozib qo‘yamiz
            request.session['user_id'] = user.id
            request.session['session_token'] = token

            return redirect('show_last_message')

        except User.DoesNotExist:
            messages.error(request, "Foydalanuvchi yoki parol noto‘g‘ri!")

    return render(request, 'login.html')


def logout_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            user.session_token = None  # ⛔ Tokenni tozalaymiz
            user.save()
        except User.DoesNotExist:
            pass

    request.session.flush()  # 🔐 Sessionni tozalaymiz
    return redirect('login')

@csrf_exempt
def edit_message(request, msg_id):
    user_id = request.session.get('user_id')
    message = get_object_or_404(MessageUser, id=msg_id, taken_by_id=user_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_text = data.get('text', '')
            if new_text:
                message.text = new_text
                message.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Text bo‘sh'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'POST so‘rov bo‘lishi kerak'}, status=405)
def delete_message(request, msg_id):
    user_id = request.session.get('user_id')
    message = get_object_or_404(MessageUser, id=msg_id, taken_by_id=user_id)
    message.delete()
    return redirect('my_messages')

@csrf_exempt
def take_message(request, id):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'Avval tizimga kiring'}, status=401)
        try:
            msg = MessageUser.objects.get(id=id)
            if msg.taken_by is None:
                msg.taken_by_id = user_id
                msg.save()
                user = User.objects.get(id=user_id)
                return JsonResponse({'success': True, 'taken_by': user.username})
            else:
                return JsonResponse({'success': False, 'error': 'Allaqachon olingan'})
        except MessageUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Xabar topilmadi'})
    return JsonResponse({'success': False, 'error': 'Faqat POST so‘rovga ruxsat'})

