# config/asgi.py
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()  # Ilova yuklanishidan oldin routing import bo‘lmasligi kerak!

# routingni endi import qilamiz!
import account.routing

from channels.sessions import SessionMiddlewareStack  # BUNI QO‘SHISH KERAK!

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": SessionMiddlewareStack(  # <- bu orqali session ishlaydi!
        AuthMiddlewareStack(
            URLRouter(
                account.routing.websocket_urlpatterns
            )
        )
    ),
})
