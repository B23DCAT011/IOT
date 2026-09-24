"""Gửi lệnh lên topic `device_control` từ tiến trình API — 05-API.md §6.3, §7.4.

Mỗi lần gọi tạo MỘT client ngắn hạn (connect → publish → disconnect), không dùng chung
client với mqtt_worker: hai tiến trình không chia sẻ được socket (CLAUDE.md §5.1).
"""
import json
import threading

from django.conf import settings

from apps.mqtt import topics
from apps.mqtt.client import broker_address, create_client, random_client_id


class MqttPublishError(Exception):
    """Không kết nối được, sai tài khoản, hoặc broker không xác nhận PUBACK."""


def publish_control(request_id, device_code, action):
    """Gửi `{"request_id", "device", "action"}` với QoS 1 và CHỜ broker xác nhận."""
    payload = json.dumps({
        "request_id": str(request_id),   # UUID → chuỗi 36 ký tự
        "device": device_code,           # mã `code`, KHÔNG phải id số (04-Database.md §7.2)
        "action": action,
    })
    timeout = settings.MQTT_CONNECT_TIMEOUT
    connack = threading.Event()
    result = {}

    def on_connect(client, userdata, flags, reason_code, properties):
        result["reason"] = reason_code
        connack.set()

    client = create_client(random_client_id("backend_api"))
    client.on_connect = on_connect

    try:
        client.connect(*broker_address(), keepalive=10)   # lỗi mạng → OSError ngay tại đây
        # BẮT BUỘC chạy vòng lặp mạng trước publish(qos=1): không có nó message nằm im
        # trong hàng đợi và disconnect() vứt đi — API vẫn trả 202 mà lệnh chưa rời máy chủ.
        client.loop_start()
        # connect() "thành công" cả khi sai mật khẩu — phải chờ CONNACK mới biết.
        if not connack.wait(timeout):
            raise MqttPublishError(f"Broker không trả lời CONNACK trong {timeout} giây")
        if result["reason"].is_failure:
            raise MqttPublishError(f"Broker từ chối kết nối: {result['reason']}")

        info = client.publish(topics.DEVICE_CONTROL, payload,
                              qos=topics.QOS[topics.DEVICE_CONTROL], retain=topics.RETAIN)
        info.wait_for_publish(timeout)
        if not info.is_published():
            raise MqttPublishError(f"Broker không xác nhận PUBACK trong {timeout} giây")
    except MqttPublishError:
        raise
    except (OSError, ValueError, RuntimeError) as exc:
        raise MqttPublishError(str(exc)) from exc
    finally:
        client.disconnect()    # để vòng lặp mạng kịp gửi gói DISCONNECT rồi mới dừng nó
        client.loop_stop()
