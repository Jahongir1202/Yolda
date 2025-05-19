# admin.py
from django.utils.html import mark_safe
from django.contrib import admin
from .models import TelegramAccount, Message, User

# admin.py
from .models import TelegramGroup
admin.site.register(User)
@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'group_id', 'account')
    search_fields = ('title', 'group_id')

@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'is_logged_in', 'qr_code_preview')
    readonly_fields = ('qr_code_preview',)

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return mark_safe(f'<img src="{obj.qr_code.url}" width="150"/>')
        return "(No QR Code)"

    qr_code_preview.short_description = "QR Code"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at', 'status')
    list_filter = ('status',)
from .models import MessageUser

class MessageUserAdmin(admin.ModelAdmin):
    list_display = ('text', 'taken_by', 'created_at')
    list_filter = ('taken_by',)
admin.site.register(MessageUser, MessageUserAdmin)