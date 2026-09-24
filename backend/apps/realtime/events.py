"""Hai sự kiện WebSocket của hệ thống và hàm phát chúng — 05-API.md §5.2, §5.3.

Đây là chỗ DUY NHẤT định nghĩa hình dạng sự kiện. MQTT worker gọi `broadcast(...)`,
Redis chuyển sang tiến trình daphne, consumer đẩy nguyên dict ra trình duyệt.

⚠️ Khóa `type` vừa là tên sự kiện Frontend nhận, vừa là khóa định tuyến của Channels:
`"sensor.data"` → phương thức `sensor_data()` của consumer. Đổi tên phải đổi cả hai chỗ.
"""
from datetime import timezone as dt_timezone

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

GROUP = "realtime"   # một nhóm cho toàn hệ thống — một phòng, mọi client quan tâm mọi sự kiện

SENSOR_DATA = "sensor.data"
DEVICE_STATE = "device.state"


def broadcast(event):
    """Gửi tới mọi trình duyệt đang mở. Worker là mã đồng bộ nên bọc bằng async_to_sync."""
    async_to_sync(get_channel_layer().group_send)(GROUP, event)


def iso_utc(moment):
    """`2026-08-17T10:30:02.451231Z` — cùng định dạng với REST API (05-API.md §2.4)."""
    return moment.astimezone(dt_timezone.utc).isoformat().replace("+00:00", "Z")


def sensor_data_event(cycle):
    """Một chu kỳ = MỘT sự kiện, dù CSDL nhận 3 bản ghi. Cảm biến thiếu số đo → null."""
    return {
        "type": SENSOR_DATA,
        "device_id": cycle.node_id,                  # mã node (chuỗi), không phải id thiết bị
        **cycle.values_by_metric(),                  # temperature, humidity, light
        "recorded_at": iso_utc(cycle.recorded_at),   # chung cho cả chu kỳ (BR-11)
    }


def device_state_event(record):
    """Kết cục của MỘT lệnh — SUCCESS (SD-02) hoặc FAILED do hết giờ (SD-05).

    Timeout không có sự kiện riêng: Frontend dùng một hàm cho mọi kết cục.
    Ở nhánh FAILED, `current_state` là giá trị CŨ (không đổi).
    """
    device = record.device
    return {
        "type": DEVICE_STATE,
        "device_id": device.id,
        "device": device.code,
        "current_state": device.current_state,
        "request_id": str(record.request_id),
        "status": record.status,
        "error_message": record.error_message,
    }


def device_sync_event(device):
    """Trạng thái đổi vì thiết bị tự báo (sau mất điện), KHÔNG gắn với lệnh nào → request_id null.

    Frontend không phải sửa: sự kiện device.state nào cũng cập nhật công tắc, chỉ phần
    mở khoá công tắc mới cần khớp request_id (05-API.md §5.4 quy tắc 4).
    """
    return {
        "type": DEVICE_STATE,
        "device_id": device.id,
        "device": device.code,
        "current_state": device.current_state,
        "request_id": None,
        "status": "SUCCESS",
        "error_message": None,
    }
