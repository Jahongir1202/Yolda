# routing
from django.urls import re_path
from . import consumers  # faqat shu import, lekin consumer ichida model import bo‘lishi normal holat
websocket_urlpatterns = [
    re_path(r'ws/messages/$', consumers.MessageConsumer.as_asgi()),
]
