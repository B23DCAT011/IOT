"""Việc cần làm khi nhận một message — mỗi topic một hàm, gọi từ mqtt_worker.

Mọi hàm đều theo cùng một khuôn:  parse JSON → gọi service (ghi CSDL) → phát sự kiện WebSocket.
Logic nghiệp vụ nằm ở `apps/*/services.py`; file này chỉ nối MQTT với service.
"""
import json
import logging

from apps.devices import services as device_services
from apps.realtime import events
from apps.sensors import services as sensor_services

logger = logging.getLogger(__name__)


def parse_json_object(topic, payload):
    """JSON hỏng → ghi log và trả None, KHÔNG ném lỗi: worker không được dừng (NFR-16, UC-07 E4)."""
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        logger.warning("Bỏ qua message hỏng trên '%s': %r", topic, payload[:200])
        return None
    if not isinstance(data, dict):
        logger.warning("Bỏ qua message trên '%s': phải là một object JSON, nhận %r", topic, data)
        return None
    return data


def handle_data_sensors(payload, catalog):
    """Topic `data_sensors` — SD-03, UC-07. Một message → tối đa 3 bản ghi → một sự kiện."""
    data = parse_json_object("data_sensors", payload)
    if data is None:
        return
    cycle = sensor_services.record_cycle(data, catalog)
    if cycle.readings:
        events.broadcast(events.sensor_data_event(cycle))
    else:
        logger.warning("Message data_sensors không có số đo hợp lệ nào: %s", data)


def handle_device_respond(payload):
    """Topic `device_respond` — hai loại gói:

    - `status: "REPORT"`, không có request_id: thiết bị tự báo trạng thái thật khi
      (kết nối lại) broker → đồng bộ current_state (sau mất điện).
    - còn lại: phản hồi cho một lệnh (SD-02) → lệnh kết thúc.
    Cả hai đều báo mọi trình duyệt bằng sự kiện device.state.
    """
    data = parse_json_object("device_respond", payload)
    if data is None:
        return

    if data.get("status") == device_services.STATE_REPORT:
        device = device_services.sync_reported_state(data.get("device"), data.get("state"))
        if device is not None:
            events.broadcast(events.device_sync_event(device))
        return

    record = device_services.confirm_command(
        request_id=data.get("request_id"),
        device_code=data.get("device"),
        state=data.get("state"),
        status=data.get("status"),
    )
    if record is not None:
        events.broadcast(events.device_state_event(record))


def handle_timeouts():
    """Vòng quét mỗi 1 giây — SD-05, BR-03. Không phải message MQTT nhưng cùng khuôn."""
    for record in device_services.expire_pending_commands():
        events.broadcast(events.device_state_event(record))
