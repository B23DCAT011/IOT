"""Worker nhận message MQTT — handlers.py. Không cần broker: gọi thẳng hàm xử lý với payload bytes."""
import json
from unittest import mock

from django.test import TestCase

from apps.devices import services as device_services
from apps.devices.models import ActionHistory, Device
from apps.sensors.models import SensorData
from apps.sensors.services import SensorCatalog
from apps.users.models import User

from . import handlers


@mock.patch("apps.mqtt.handlers.events.broadcast")
class HandlerTests(TestCase):

    def setUp(self):
        self.catalog = SensorCatalog.load()

    def test_data_sensors_saves_cycle_and_broadcasts_one_event(self, broadcast):
        payload = json.dumps({"device_id": "esp8266_room01", "temperature": 28.5,
                              "light": 350, "timestamp": "bỏ qua"}).encode()
        handlers.handle_data_sensors(payload, self.catalog)

        self.assertEqual(SensorData.objects.count(), 2)
        event = broadcast.call_args.args[0]
        self.assertEqual(event["type"], "sensor.data")
        self.assertEqual(event["device_id"], "esp8266_room01")
        self.assertEqual((event["temperature"], event["humidity"], event["light"]), (28.5, None, 350.0))
        self.assertTrue(event["recorded_at"].endswith("Z"))

    def test_malformed_json_does_not_raise(self, broadcast):                 # NFR-16, UC-07 E4
        handlers.handle_data_sensors(b"{khong phai json", self.catalog)
        handlers.handle_data_sensors(b"[1, 2, 3]", self.catalog)
        handlers.handle_device_respond(b"\xff\xfe")
        self.assertFalse(SensorData.objects.exists())
        broadcast.assert_not_called()

    def test_device_respond_broadcasts_device_state(self, broadcast):
        lamp = Device.objects.get(code="room01_lamp")
        with mock.patch("apps.devices.services.publish_control"):
            record = device_services.send_command(lamp, "ON", User.objects.get(username="admin"))

        handlers.handle_device_respond(json.dumps({
            "request_id": str(record.request_id), "device": "room01_lamp",
            "state": "ON", "status": "SUCCESS",
        }).encode())

        self.assertEqual(broadcast.call_args.args[0], {
            "type": "device.state", "device_id": lamp.id, "device": "room01_lamp",
            "current_state": "ON", "request_id": str(record.request_id),
            "status": "SUCCESS", "error_message": None,
        })

    def report(self, **fields):
        handlers.handle_device_respond(json.dumps({"status": "REPORT", **fields}).encode())

    def test_state_report_after_power_loss_syncs_to_hardware(self, broadcast):
        # Giao diện đang tin đèn ON; mạch mất điện, khởi động lại với đèn OFF và tự báo lên
        Device.objects.filter(code="room01_lamp").update(current_state="ON")
        self.report(device="room01_lamp", state="OFF")

        lamp = Device.objects.get(code="room01_lamp")
        self.assertEqual(lamp.current_state, "OFF")
        self.assertEqual(broadcast.call_args.args[0], {
            "type": "device.state", "device_id": lamp.id, "device": "room01_lamp",
            "current_state": "OFF", "request_id": None, "status": "SUCCESS", "error_message": None,
        })
        self.assertFalse(ActionHistory.objects.exists())       # không phải lệnh — không ghi lịch sử

    def test_state_report_without_change_is_silent(self, broadcast):
        self.report(device="room01_lamp", state="OFF")          # seed đã là OFF
        broadcast.assert_not_called()

    def test_invalid_state_report_is_ignored(self, broadcast):
        self.report(device="room01_lamp", state="SANG")
        self.report(device="khong_ton_tai", state="ON")
        broadcast.assert_not_called()
        self.assertEqual(Device.objects.get(code="room01_lamp").current_state, "OFF")

    def test_timeout_sweep_broadcasts_failed(self, broadcast):
        lamp = Device.objects.get(code="room01_lamp")
        ActionHistory.objects.create(device=lamp, action="ON")
        ActionHistory.objects.update(
            created_at=device_services.timezone.now() - device_services.timedelta(seconds=6))

        handlers.handle_timeouts()

        event = broadcast.call_args.args[0]
        self.assertEqual((event["status"], event["current_state"]), ("FAILED", "OFF"))
        self.assertIn("Timeout", event["error_message"])
