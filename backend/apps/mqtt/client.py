"""Một chỗ duy nhất tạo client paho-mqtt — dùng cho cả API (publish) lẫn worker (subscribe)."""
import uuid

import paho.mqtt.client as mqtt
from django.conf import settings


def create_client(client_id):
    """Client đã gắn tài khoản broker (NFR-09: broker tắt anonymous)."""
    # paho-mqtt 2.x bắt buộc tham số CallbackAPIVersion (05-API.md §7.4 điểm 2)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    if settings.MQTT_USERNAME:
        client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
    client.connect_timeout = settings.MQTT_CONNECT_TIMEOUT    # broker chết không treo request
    return client


def random_client_id(prefix):
    """`backend_api_3f2b8c1e` — ID trùng thì broker đá kết nối cũ ra (05-API.md §6.1)."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def broker_address():
    return settings.MQTT_HOST, settings.MQTT_PORT
