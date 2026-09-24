"""WebSocket /ws/realtime/ — ca A-23 và việc chuyển sự kiện từ channel layer ra trình duyệt.

Dùng InMemoryChannelLayer: đủ cho test trong MỘT tiến trình, không cần Redis.
TransactionTestCase vì middleware đọc token ở một luồng khác (database_sync_to_async).
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from channels_redis.core import RedisChannelLayer
from django.conf import settings
from django.test import SimpleTestCase, TransactionTestCase, override_settings
from rest_framework.authtoken.models import Token

from apps.users.models import User
from config.asgi import application

from .events import GROUP

IN_MEMORY = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
ORIGIN = [(b"origin", b"http://localhost:5173")]


class RedisTimeoutConfigTests(SimpleTestCase):
    def test_read_timeout_longer_than_channel_wait(self):
        # redis-py 8 mặc định chờ đọc 5 giây = đúng thời gian channels_redis chờ tin mới.
        # Bằng hoặc ngắn hơn thì WebSocket sập sau mỗi 5 giây không có sự kiện (mạch ngoại tuyến).
        host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
        self.assertGreater(host["socket_timeout"], RedisChannelLayer.brpop_timeout)


@override_settings(CHANNEL_LAYERS=IN_MEMORY)
class RealtimeConsumerTests(TransactionTestCase):

    def setUp(self):
        user = User.objects.create_user("tester", password="x")
        self.token = Token.objects.create(user=user).key

    def test_A23_bad_token_is_accepted_then_closed_4401(self):
        async_to_sync(self._assert_closed_with_4401)("/ws/realtime/?token=sai")
        async_to_sync(self._assert_closed_with_4401)("/ws/realtime/")

    async def _assert_closed_with_4401(self, path):
        ws = WebsocketCommunicator(application, path, headers=ORIGIN)
        connected, _ = await ws.connect()
        self.assertTrue(connected)                         # accept() trước…
        output = await ws.receive_output()
        self.assertEqual(output, {"type": "websocket.close", "code": 4401})   # …rồi mới đóng
        await ws.disconnect()

    def test_group_event_reaches_browser(self):
        async_to_sync(self._assert_event_forwarded)()

    async def _assert_event_forwarded(self):
        ws = WebsocketCommunicator(application, f"/ws/realtime/?token={self.token}", headers=ORIGIN)
        connected, _ = await ws.connect()
        self.assertTrue(connected)

        event = {"type": "device.state", "device_id": 1, "status": "SUCCESS"}
        await get_channel_layer().group_send(GROUP, event)
        self.assertEqual(await ws.receive_json_from(), event)
        await ws.disconnect()
