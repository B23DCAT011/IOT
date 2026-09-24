"""Kênh WebSocket /ws/realtime/ — 05-API.md §5.1, §7.6.

Một chiều: chỉ máy chủ → trình duyệt. Không gửi gì lúc vừa kết nối — trạng thái ban đầu
do các lời gọi HTTP của Dashboard dựng lên, WebSocket chỉ lo các thay đổi tiếp theo.
"""
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .events import GROUP

logger = logging.getLogger(__name__)

CLOSE_UNAUTHORIZED = 4401   # dải 4000–4999 dành cho ứng dụng; chọn giống 401 cho dễ nhớ


class RealtimeConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        # PHẢI accept() rồi mới close(4401). Đóng trước accept() thì trình duyệt chỉ thấy
        # mã 1006 chung chung, Frontend tưởng máy chủ tắt và thử kết nối lại mãi mãi.
        await self.accept()
        if self.scope["user"].is_anonymous:
            await self.close(code=CLOSE_UNAUTHORIZED)
            return
        await self.channel_layer.group_add(GROUP, self.channel_name)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(GROUP, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Không có thao tác nghiệp vụ nào đi theo chiều này — điều khiển dùng HTTP POST
        # để còn nhận được mã lỗi 400/404/409/503.
        logger.info("Bỏ qua message từ client: %s", content)

    # Tên phương thức = giá trị "type" của sự kiện, dấu chấm đổi thành gạch dưới.
    async def sensor_data(self, event):
        await self.send_json(event)

    async def device_state(self, event):
        await self.send_json(event)
