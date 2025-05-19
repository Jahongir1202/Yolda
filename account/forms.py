from django import forms
from .models import TelegramGroup

class SendMessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), label='Xabar')
    group = forms.ModelChoiceField(queryset=TelegramGroup.objects.all(), label='Guruhni tanlang')
