import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import authentication.routing  # Your app's routing.py

import os
from django.core.asgi import get_asgi_application

# Make sure settings are properly configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WaterTankRefillSystem.settings')

application = get_asgi_application()


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            authentication.routing.websocket_urlpatterns  # <-- Make sure this matches
        )
    ),
})
