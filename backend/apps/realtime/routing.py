from django.urls import path

from .consumers import RealtimeConsumer

# Có dấu "/" cuối — ngoại lệ duy nhất so với REST (05-API.md §2.5)
websocket_urlpatterns = [
    path("ws/realtime/", RealtimeConsumer.as_asgi()),
]
