"""Bảng định tuyến HTTP — 05-API.md §3, §7.2. WebSocket nằm ở apps/realtime/routing.py."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.core.views import ProfileView
from apps.devices.views import ActionHistoryViewSet, DeviceViewSet
from apps.sensors.views import SensorViewSet
from apps.users.views import LoginView, LogoutView

# trailing_slash=False BẮT BUỘC: có "/" cuối thì POST thiếu "/" bị chuyển hướng 301
# và trình duyệt gửi lại bằng GET — lệnh điều khiển mất body một cách im lặng (§2.5).
router = DefaultRouter(trailing_slash=False)
router.include_root_view = False
router.register("sensors", SensorViewSet, basename="sensors")
router.register("devices", DeviceViewSet, basename="devices")
router.register("actions", ActionHistoryViewSet, basename="actions")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/profile", ProfileView.as_view(), name="profile"),
    path("api/auth/login", LoginView.as_view(), name="login"),
    path("api/auth/logout", LogoutView.as_view(), name="logout"),
    # Tài liệu API — mở được khi chưa đăng nhập (§3.3)
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("admin/", admin.site.urls),
]
