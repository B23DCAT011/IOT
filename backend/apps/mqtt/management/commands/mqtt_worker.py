"""Tiến trình 2 — `python manage.py mqtt_worker` (CLAUDE.md §5.1).

Django không giữ được vòng lặp MQTT trong tiến trình web, nên việc NHẬN message chạy ở đây:

    data_sensors   (QoS 0) → handlers.handle_data_sensors   → sự kiện sensor.data
    device_respond (QoS 1) → handlers.handle_device_respond → sự kiện device.state
    mỗi 1 giây             → handlers.handle_timeouts       → sự kiện device.state (FAILED)

Hai luồng: luồng mạng của paho gọi on_message; luồng chính chạy vòng quét timeout.
Sửa ngưỡng hoặc thêm cảm biến trong CSDL → phải khởi động lại lệnh này (danh mục nạp một lần).
"""
import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError, connection

from apps.mqtt import handlers, topics
from apps.mqtt.client import broker_address, create_client
from apps.sensors.services import SensorCatalog

logger = logging.getLogger("apps.mqtt.worker")

CLIENT_ID = "backend_worker"   # 05-API.md §6.1 — chỉ chạy MỘT worker


class Command(BaseCommand):
    help = "Nhận số đo và phản hồi thiết bị từ MQTT, ghi CSDL, đẩy WebSocket; quét lệnh hết giờ."

    def handle(self, *args, **options):
        catalog = SensorCatalog.load()
        logger.info("Đã nạp %d cảm biến trong danh mục", len(catalog))
        self.routes = {
            topics.DATA_SENSORS: lambda payload: handlers.handle_data_sensors(payload, catalog),
            topics.DEVICE_RESPOND: handlers.handle_device_respond,
        }

        client = create_client(CLIENT_ID)
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        client.on_message = self.on_message
        client.reconnect_delay_set(min_delay=1, max_delay=10)
        # connect_async: broker chưa bật cũng không sao, paho tự thử lại trong nền
        client.connect_async(*broker_address(), keepalive=30)
        client.loop_start()
        logger.info("Kết nối tới broker %s:%s…", *broker_address())

        try:
            while True:
                time.sleep(settings.TIMEOUT_SWEEP_INTERVAL_SECONDS)
                self.run_safely("quét timeout", handlers.handle_timeouts)
        except KeyboardInterrupt:
            logger.info("Dừng mqtt_worker")
        finally:
            client.disconnect()
            client.loop_stop()

    # ----- callback của paho (chạy trên luồng mạng) -----

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.error("Broker từ chối kết nối: %s (kiểm tra MQTT_USERNAME/PASSWORD)", reason_code)
            return
        # Đăng ký lại MỖI lần kết nối: mất kết nối rồi nối lại thì broker không nhớ subscription cũ
        for topic in self.routes:
            client.subscribe(topic, qos=topics.QOS[topic])
        logger.info("Đã kết nối broker, subscribe: %s", ", ".join(self.routes))

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning("Mất kết nối broker (%s) — paho tự kết nối lại", reason_code)

    def on_message(self, client, userdata, message):
        handler = self.routes.get(message.topic)
        if handler is not None:
            self.run_safely(message.topic, handler, message.payload)

    # ----- tiện ích -----

    @staticmethod
    def run_safely(label, func, *args):
        """Một message lỗi không được làm chết worker (NFR-16).

        Ngoại lệ lọt ra khỏi callback sẽ giết luồng mạng của paho — nên bắt hết ở đây.
        """
        try:
            func(*args)
        except DatabaseError:
            logger.exception("Lỗi CSDL khi xử lý %s — đóng kết nối, lần sau tự mở lại", label)
            connection.close()
        except Exception:
            logger.exception("Lỗi khi xử lý %s", label)
