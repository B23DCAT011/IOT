"""Xác thực WebSocket bằng `?token=` — 05-API.md §5.1, §7.6.

Trình duyệt không cho đặt header cho WebSocket, nên token đi trên URL.
Middleware chỉ gắn `scope["user"]`; việc từ chối (đóng mã 4401) là của consumer.
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user_for_token(key):
    try:
        user = Token.objects.select_related("user").get(key=key).user
    except Token.DoesNotExist:
        return AnonymousUser()
    return user if user.is_active else AnonymousUser()   # giống TokenAuthentication


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        key = query.get("token", [None])[0]
        scope["user"] = await get_user_for_token(key) if key else AnonymousUser()
        return await super().__call__(scope, receive, send)
