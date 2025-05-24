from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import User, MessageUser, TelegramAccount, Message
import json
from .tasks import delete_message
from datetime import timedelta
@csrf_exempt
def send_to_groups(request, msg_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            print(f"Xabar yuborilyapti: {message} (msg_id={msg_id})")

            if not message:
                return JsonResponse({'success': False, 'error': 'Xabar bo‘sh!'}, status=400)

            accounts = TelegramAccount.objects.filter(is_default=True)
            for account in accounts:
                account.send_message_to_groups(message)

            return JsonResponse({'success': True, 'msg_id': msg_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'error': 'POST so‘rov bo‘lishi kerak'}, status=405)

def show_last_message(request):
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

def my_messages_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    my_messages = MessageUser.objects.filter(taken_by_id=user_id).order_by('-created_at')
    return render(request, 'my_messages.html', {'messages': my_messages})

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


