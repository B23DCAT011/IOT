"""Thiết bị và lịch sử — ca A-08 → A-15, cùng vòng đời PENDING → SUCCESS/FAILED.

Hàm publish MQTT được thay bằng mock: các ca này chạy không cần Mosquitto.
"""
from datetime import timedelta
from unittest import mock

from apps.core.testing import LoggedInAPITestCase

from . import services
from .models import ActionHistory, Device
from .mqtt_publisher import MqttPublishError

LAMP = 1   # room01_lamp — id do migration seed tạo


@mock.patch("apps.devices.services.publish_control")
class ControlTests(LoggedInAPITestCase):

    def control(self, action="ON", device_id=LAMP, **extra):
        return self.client.post(f"/api/devices/{device_id}/control", {"action": action, **extra},
                                format="json")

    def test_A08_device_list_is_plain_array(self, publish):
        data = self.client.get("/api/devices").data
        self.assertEqual([d["code"] for d in data], ["room01_lamp", "room01_fan"])
        self.assertEqual(data[0]["current_state"], "OFF")

    def test_A09_unknown_or_inactive_device_is_404(self, publish):
        self.assertError(self.control(device_id=999), 404, "NOT_FOUND")
        Device.objects.filter(pk=LAMP).update(is_active=False)
        self.assertError(self.control(), 404, "NOT_FOUND")
        publish.assert_not_called()

    def test_A10_invalid_action_is_400(self, publish):
        error = self.assertError(self.control("TOGGLE"), 400, "VALIDATION_ERROR")
        self.assertIn("action", error["details"])

    def test_A11_lowercase_action_accepted_202(self, publish):
        response = self.control("on")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["action"], "ON")
        self.assertEqual(response.data["status"], "PENDING")
        self.assertEqual(response.data["device"], "room01_lamp")
        self.assertEqual(response.data["user"], {"id": self.admin.id, "full_name": "Lưu Đức Anh"})
        publish.assert_called_once()
        self.assertEqual(publish.call_args.args[1:], ("room01_lamp", "ON"))

    def test_A11c_user_comes_from_token_not_body(self, publish):
        self.login_as(self.operator)
        response = self.control("ON", user_id=self.admin.id)
        self.assertEqual(response.data["user"]["full_name"], "Người vận hành")

    def test_A11d_no_token_no_record(self, publish):
        self.logout()
        self.assertError(self.control(), 401, "UNAUTHENTICATED")
        self.assertFalse(ActionHistory.objects.exists())

    def test_A12_broker_down_is_503_and_rolls_back(self, publish):
        publish.side_effect = MqttPublishError("broker tắt")
        self.assertError(self.control(), 503, "BROKER_UNAVAILABLE")
        self.assertFalse(ActionHistory.objects.exists())

    def test_A13_second_command_while_pending_is_409(self, publish):
        self.assertEqual(self.control().status_code, 202)
        self.assertError(self.control("OFF"), 409, "DEVICE_BUSY")
        self.assertEqual(ActionHistory.objects.count(), 1)

    def test_A14_after_timeout_device_accepts_again(self, publish):
        self.control()
        ActionHistory.objects.update(created_at=services.timezone.now() - timedelta(seconds=6))
        expired = services.expire_pending_commands()

        self.assertEqual(len(expired), 1)
        record = ActionHistory.objects.get()
        self.assertEqual(record.status, "FAILED")
        self.assertIsNotNone(record.responded_at)
        self.assertIn("Timeout", record.error_message)
        self.assertEqual(Device.objects.get(pk=LAMP).current_state, "OFF")   # giữ nguyên
        self.assertEqual(self.control().status_code, 202)


@mock.patch("apps.devices.services.publish_control")
class ConfirmCommandTests(LoggedInAPITestCase):
    """Worker nhận `device_respond` — SD-02, UC-02 E5."""

    def setUp(self):
        super().setUp()
        self.lamp = Device.objects.get(pk=LAMP)

    def send(self):
        return services.send_command(self.lamp, "ON", self.admin)

    def test_success_updates_current_state(self, publish):
        record = self.send()
        done = services.confirm_command(str(record.request_id), "room01_lamp", "ON", "SUCCESS")
        self.assertEqual(done.status, "SUCCESS")
        self.assertIsNotNone(done.latency_ms)
        self.assertEqual(Device.objects.get(pk=LAMP).current_state, "ON")
        self.assertEqual(ActionHistory.objects.get().user, self.admin)   # user không bị đụng

    def test_duplicate_or_late_respond_is_ignored(self, publish):
        record = self.send()
        services.confirm_command(record.request_id, "room01_lamp", "ON", "SUCCESS")
        self.assertIsNone(services.confirm_command(record.request_id, "room01_lamp", "ON", "SUCCESS"))

    def test_unknown_or_malformed_request_id_is_ignored(self, publish):
        self.assertIsNone(services.confirm_command("khong-phai-uuid", "room01_lamp", "ON", "SUCCESS"))
        self.assertIsNone(services.confirm_command("3f2b8c1e-9a4d-4f7b-8c21-0e5d6a7b8c90",
                                                   "room01_lamp", "ON", "SUCCESS"))

    def test_device_reports_failure(self, publish):
        record = self.send()
        done = services.confirm_command(record.request_id, "room01_lamp", "OFF", "ERROR")
        self.assertEqual(done.status, "FAILED")
        self.assertEqual(Device.objects.get(pk=LAMP).current_state, "OFF")


class ActionHistoryListTests(LoggedInAPITestCase):
    """UC-05 và UC-04 trên bảng lịch sử."""

    def setUp(self):
        super().setUp()
        lamp, fan = Device.objects.order_by("id")
        now = services.timezone.now()
        # Một bản ghi không qua API (user NULL — như lệnh gõ bằng mosquitto_pub) và hai bản ghi có người
        ActionHistory.objects.create(device=fan, action="OFF", status="SUCCESS", responded_at=now)
        ActionHistory.objects.create(device=lamp, action="ON", user=self.admin,
                                     status="FAILED", responded_at=now, error_message="Timeout")
        ActionHistory.objects.create(device=lamp, action="ON", user=self.operator)

    def results(self, query=""):
        return self.client.get(f"/api/actions{query}").data["results"]

    def test_newest_first_with_nested_objects(self):
        first = self.results()[0]
        self.assertEqual(first["device"], {"id": 1, "code": "room01_lamp", "name": "Đèn phòng"})
        self.assertEqual(first["status"], "PENDING")
        self.assertIsNone(first["latency_ms"])

    def test_A11e_user_none_lists_records_without_user(self):
        rows = self.results("?user=none")
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["user"])

    def test_filter_by_user_status_device_and_search(self):
        self.assertEqual(len(self.results(f"?user={self.operator.id}")), 1)
        self.assertEqual(len(self.results("?status=FAILED")), 1)
        self.assertEqual(len(self.results("?device=2")), 1)
        self.assertEqual(len(self.results("?search=Quạt")), 1)
        self.assertEqual(len(self.results("?search=Người vận")), 1)

    def test_invalid_filters(self):
        self.assertError(self.client.get("/api/actions?user=abc"), 400, "VALIDATION_ERROR")
        self.assertError(self.client.get("/api/actions?status=DONE"), 400, "VALIDATION_ERROR")
        url = ("/api/actions?created_at__gte=2026-08-18T00:00:00%2B07:00"
               "&created_at__lte=2026-08-17T00:00:00%2B07:00")
        self.assertError(self.client.get(url), 400, "INVALID_RANGE")
