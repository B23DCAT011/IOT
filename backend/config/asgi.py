"""Điểm vào của tiến trình 1 (`daphne config.asgi:application`) — HTTP + WebSocket cùng cổng 8000."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# ⚠️ Phải gọi get_asgi_application() TRƯỚC khi import bất cứ thứ gì đụng tới model
# (TokenAuthMiddleware import Token) — sai thứ tự thì báo AppRegistryNotReady.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from django.conf import settings  # noqa: E402
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler  # noqa: E402

from apps.realtime.auth import TokenAuthMiddleware  # noqa: E402
from apps.realtime.routing import websocket_urlpatterns  # noqa: E402

# Khi DEBUG, tự phục vụ file tĩnh của trang admin (daphne không làm việc này).
http_app = ASGIStaticFilesHandler(django_asgi_app) if settings.DEBUG else django_asgi_app

application = ProtocolTypeRouter({
    "http": http_app,
    # Origin của trình duyệt phải nằm trong ALLOWED_HOSTS, nếu không kết nối bị từ chối
    # ngay (05-API.md §2.9). Demo trong LAN: thêm IP laptop vào ALLOWED_HOSTS.
    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddleware(URLRouter(websocket_urlpatterns))
    ),
})
