from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import User, MessageUser, TelegramAccount, Message, ArxivMessage
import json
from .tasks import delete_message
from datetime import timedelta


# views.py
@csrf_exempt
def show_last_message(request):
    if request.method == 'POST':
        qayerda = request.POST.get('qayerda')
        qayerga = request.POST.get('qayerga')
        cars = request.POST.get('cars')
        text = request.POST.get('text')
        narxi = request.POST.get('narxi')

        print("POST ma'lumotlari:", qayerda, qayerga, cars, text, narxi)

        if all([qayerda, qayerga, cars, text, narxi]):
            arxiv = ArxivMessage.objects.create(
                qayerda=qayerda,
                qayerga=qayerga,
                cars=cars,
                text=text,
                narxi=narxi
            )
            print("✅ Yangi ma'lumot saqlandi")

            # ⬇️ Telegramga yuborish
            message = (
                f"Qayerda: {arxiv.qayerda}\n"
                f"Qayerga: {arxiv.qayerga}\n"
                f"Avtomobil: {arxiv.cars}\n"
                f"Matn: {arxiv.text}\n"
                f"Narxi: {arxiv.narxi}"
            )
            accounts = TelegramAccount.objects.filter(is_default=True)
            for account in accounts:
                account.send_message_to_groups(message)
            print("🎉 Barcha guruhlarga yuborildi.")
        else:
            print("❌ To‘liq emas, saqlanmadi")

        return redirect('show_last_message')   # yoki kerakli sahifaga qaytish

    # GET holati
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    all_messages = MessageUser.objects.all().order_by('-created_at')
    visible_messages = [
        msg for msg in all_messages
        if msg.taken_by is None or msg.taken_by.id == user_id
    ]

    return render(request, 'list.html', {
        'messages': visible_messages,
        'user_id': user_id
    })

@csrf_exempt
def send_to_groups(request, msg_id):
    print("📥 [send_to_groups] So‘rov keldi. Method:", request.method)

    if request.method == 'POST':
        try:
            print(f"🔍 ArxivMessage obyektini topishga urinyapti. msg_id: {msg_id}")
            arxiv_msg = ArxivMessage.objects.get(id=msg_id)
            print(f"✅ ArxivMessage topildi: {arxiv_msg}")

            message = (
                f"Qayerda: {arxiv_msg.qayerda}\n"
                f"Qayerga: {arxiv_msg.qayerga}\n"
                f"Avtomobil: {arxiv_msg.cars}\n"
                f"Matn: {arxiv_msg.text}\n"
                f"Narxi: {arxiv_msg.narxi}"
            )
            print(f"📤 Yuboriladigan xabar tayyorlandi:\n{message}")

            accounts = TelegramAccount.objects.filter(is_default=True)
            print(f"🔗 Default Telegram accountlar soni: {accounts.count()}")

            for i, account in enumerate(accounts, start=1):
                print(f"➡️ [{i}] Guruhlarga yuborilyapti: account_id={account.id}")
                account.send_message_to_groups(message)
                print(f"✅ [{i}] Yuborildi")

            print("🎉 Barcha guruhlarga yuborildi.")
            return JsonResponse({'success': True, 'msg_id': msg_id})

        except ArxivMessage.DoesNotExist:
            print(f"❌ ArxivMessage topilmadi. msg_id: {msg_id}")
            return JsonResponse({'success': False, 'error': 'ArxivMessage topilmadi'}, status=404)
        except Exception as e:
            print(f"🔥 Xatolik yuz berdi: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        print("❌ Notog‘ri so‘rov turi. Faqat POST ruxsat etilgan.")
        return JsonResponse({'success': False, 'error': 'POST so‘rov bo‘lishi kerak'}, status=405)

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
            request.session['user_id'] = user.id
            return redirect('show_last_message')
        except User.DoesNotExist:
            messages.error(request, "Foydalanuvchi yoki parol noto'g'ri!")
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect("login")


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

