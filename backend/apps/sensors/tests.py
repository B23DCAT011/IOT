"""Cảm biến: ghi một chu kỳ (UC-07) và 4 endpoint /api/sensors — ca A-00 → A-07f."""
from datetime import timedelta
from unittest import mock

from django.utils import timezone

from apps.core.testing import LoggedInAPITestCase

from .models import SensorData, SensorDevice
from .services import SensorCatalog, next_alert_state, record_cycle, update_alert_states

FULL = {"device_id": "esp8266_room01", "temperature": 28.5, "humidity": 72.0, "light": 350}


class SensorTestCase(LoggedInAPITestCase):
    def setUp(self):
        super().setUp()
        self.catalog = SensorCatalog.load()

    def record(self, payload=FULL, at=None):
        """Ghi một chu kỳ; `at` cho phép đặt mốc thời gian để tạo nhiều chu kỳ khác nhau."""
        with mock.patch("apps.sensors.services.timezone.now", return_value=at or timezone.now()):
            return record_cycle(dict(payload), self.catalog)

    def record_many(self, count, payload=FULL):
        start = timezone.now() - timedelta(seconds=2 * count)
        for i in range(count):
            self.record(payload, at=start + timedelta(seconds=2 * i))


class RecordCycleTests(SensorTestCase):
    """UC-07 — worker tách một message thành nhiều bản ghi."""

    def test_one_message_three_rows_same_timestamp(self):            # BR-11
        cycle = self.record()
        self.assertEqual(SensorData.objects.count(), 3)
        self.assertEqual(SensorData.objects.values("recorded_at").distinct().count(), 1)
        self.assertEqual(cycle.values_by_metric(),
                         {"temperature": 28.5, "humidity": 72.0, "light": 350.0})

    def test_missing_field_writes_no_row(self):                        # UC-07 A2
        cycle = self.record({"temperature": 28.4, "light": 352})
        self.assertEqual(SensorData.objects.count(), 2)
        self.assertIsNone(cycle.values_by_metric()["humidity"])

    def test_out_of_range_drops_only_that_reading(self):               # UC-07 E3
        self.record({"temperature": 99, "humidity": 70, "light": 300})
        self.assertEqual(sorted(SensorData.objects.values_list("sensor__code", flat=True)),
                         ["room01_humi", "room01_lux"])

    def test_non_number_and_unknown_field_ignored(self):               # UC-07 E4, E5
        self.record({"temperature": "abc", "humidity": True, "light": 300, "pressure": 1000})
        self.assertEqual(list(SensorData.objects.values_list("sensor__code", flat=True)), ["room01_lux"])


class SensorEndpointTests(SensorTestCase):

    def test_A00_catalog_is_plain_array(self):
        response = self.client.get("/api/sensors/devices")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([s["code"] for s in response.data], ["room01_temp", "room01_humi", "room01_lux"])
        self.assertEqual(set(response.data[0]), {
            "id", "code", "name", "metric_type", "unit", "node_id", "min_value", "max_value",
            "alert_enabled", "alert_low", "alert_high", "alert_state",
            "alert_updated_at", "alert_updated_by", "alert_device",
        })
        self.assertFalse(response.data[0]["alert_enabled"])     # mặc định chưa bật cảnh báo

    def test_A01_latest_empty_is_empty_array(self):
        response = self.client.get("/api/sensors/latest")
        self.assertEqual((response.status_code, response.data), (200, []))

    def test_A02_latest_one_item_per_sensor(self):
        self.record_many(3)
        newest = self.record({"temperature": 30.1, "humidity": 60.0, "light": 500})
        data = self.client.get("/api/sensors/latest").data
        self.assertEqual([item["sensor"]["code"] for item in data], ["room01_temp", "room01_humi", "room01_lux"])
        self.assertEqual([item["value"] for item in data], [30.1, 60.0, 500.0])
        self.assertEqual({item["recorded_at"] for item in data},
                         {newest.recorded_at.isoformat().replace("+00:00", "Z")})

    def test_A02b_list_orders_temp_humi_lux_within_cycle(self):
        self.record()
        data = self.client.get("/api/sensors").data
        self.assertEqual(data["count"], 3)
        self.assertEqual([r["sensor"]["code"] for r in data["results"]],
                         ["room01_temp", "room01_humi", "room01_lux"])
        self.assertTrue(data["results"][0]["recorded_at"].endswith("Z"))   # TIME_ZONE = UTC

    def test_A03_chart_ascending_with_three_keys(self):
        self.record_many(25)
        data = self.client.get("/api/sensors/chart").data
        self.assertEqual(len(data), 20)                                  # BR-10
        stamps = [p["recorded_at"] for p in data]
        self.assertEqual(stamps, sorted(stamps))
        self.assertEqual(set(data[0]), {"recorded_at", "temperature", "humidity", "light"})

    def test_A03b_chart_keeps_cycle_with_missing_reading(self):
        self.record_many(2)
        self.record({"temperature": 28.4, "light": 352})
        last = self.client.get("/api/sensors/chart").data[-1]
        self.assertEqual((last["temperature"], last["humidity"]), (28.4, None))

    def test_chart_limit_validation(self):
        self.assertError(self.client.get("/api/sensors/chart?limit=abc"), 400, "VALIDATION_ERROR")
        self.record_many(3)
        self.assertEqual(len(self.client.get("/api/sensors/chart?limit=500").data), 3)

    def test_requires_token(self):
        self.logout()
        self.assertError(self.client.get("/api/sensors/latest"), 401, "UNAUTHENTICATED")


class SensorListFilterTests(SensorTestCase):
    """UC-04 trên bảng Data Sensor."""

    def test_A04_page_size_clamped_to_100(self):
        self.record_many(35)                                             # 105 bản ghi
        self.assertEqual(len(self.client.get("/api/sensors?page_size=500").data["results"]), 100)

    def test_A05_page_size_wrong_type_is_400(self):
        error = self.assertError(self.client.get("/api/sensors?page_size=abc"), 400, "VALIDATION_ERROR")
        self.assertIn("page_size", error["details"])

    def test_A06_page_out_of_range_is_page_not_found(self):
        self.record()
        self.assertError(self.client.get("/api/sensors?page=99999"), 404, "PAGE_NOT_FOUND")

    def test_A07_reversed_time_range(self):
        url = ("/api/sensors?recorded_at__gte=2026-08-18T00:00:00%2B07:00"
               "&recorded_at__lte=2026-08-17T00:00:00%2B07:00")
        error = self.assertError(self.client.get(url), 400, "INVALID_RANGE")
        self.assertEqual(list(error["details"]), ["recorded_at__gte"])

    def test_A07b_reversed_value_range(self):
        url = "/api/sensors?sensor=room01_temp&value__gte=35&value__lte=20"
        error = self.assertError(self.client.get(url), 400, "INVALID_RANGE")
        self.assertEqual(list(error["details"]), ["value__gte"])

    def test_A07c_sensor_value_and_time_combined(self):
        self.record()
        self.record({"temperature": 31, "humidity": 80, "light": 40})
        url = "/api/sensors?sensor=room01_temp&value__gte=30&recorded_at__gte=2000-01-01T00:00:00%2B07:00"
        results = self.client.get(url).data["results"]
        self.assertEqual([(r["sensor"]["code"], r["value"]) for r in results], [("room01_temp", 31.0)])

    def test_A07d_value_filter_requires_sensor(self):
        error = self.assertError(self.client.get("/api/sensors?value__gte=30"), 400, "VALIDATION_ERROR")
        self.assertIn("value__gte", error["details"])

    def test_A07e_search_by_sensor_name(self):
        self.record()
        results = self.client.get("/api/sensors", {"search": "độ ẩm"}).data["results"]
        self.assertEqual({r["sensor"]["code"] for r in results}, {"room01_humi"})

    def test_A07f_paging_by_value_never_repeats_rows(self):
        # Cùng một giá trị ở mọi chu kỳ → toàn bộ bảng hoà nhau theo `value`
        self.record_many(4)
        pages = [self.client.get(f"/api/sensors?ordering=-value&page_size=3&page={p}").data["results"]
                 for p in (1, 2, 3, 4)]
        ids = [row["id"] for page in pages for row in page]
        self.assertEqual(len(ids), len(set(ids)))

    def test_filter_by_node(self):
        self.record()
        self.assertEqual(self.client.get("/api/sensors?node=esp8266_room01").data["count"], 3)
        self.assertEqual(self.client.get("/api/sensors?node=esp8266_room02").data["count"], 0)


class AlertStateTests(SensorTestCase):
    """Worker so số đo với ngưỡng cảnh báo — next_alert_state() và update_alert_states()."""

    def setUp(self):
        super().setUp()
        self.temp = SensorDevice.objects.get(code="room01_temp")
        self.temp.alert_enabled, self.temp.alert_low, self.temp.alert_high = True, 18, 32
        self.temp.save()

    def states(self, *values):
        state, out = None, []
        for value in values:
            state = next_alert_state(self.temp, value, state)
            out.append(state)
        return out

    def test_high_low_and_back_inside(self):
        self.assertEqual(self.states(28, 32.1, 25, 17.9, 25),
                         [None, "HIGH", None, "LOW", None])

    def test_exactly_on_threshold_is_not_alert(self):
        self.assertEqual(self.states(32, 18), [None, None])

    def test_hysteresis_keeps_alert_near_threshold(self):
        # vượt 32 → cảnh báo; 31.8 vẫn trong vùng đệm 0.5 °C → còn cảnh báo; 31.4 mới thôi
        self.assertEqual(self.states(32.2, 31.8, 32.1, 31.4), ["HIGH", "HIGH", "HIGH", None])

    def test_missing_reading_keeps_state(self):                       # UC-07 A2
        self.assertEqual(self.states(33, None), ["HIGH", "HIGH"])

    def test_disabled_clears_even_without_reading(self):
        self.temp.alert_enabled = False
        self.assertIsNone(next_alert_state(self.temp, None, "HIGH"))
        self.assertIsNone(next_alert_state(self.temp, 40, None))

    def test_update_saves_only_transitions(self):
        cycle = self.record({**FULL, "temperature": 33})
        alerts, changes = update_alert_states(cycle)
        self.assertEqual(alerts, {"temperature": "HIGH", "humidity": None, "light": None})
        self.assertEqual([(c.sensor.code, c.state) for c in changes], [("room01_temp", "HIGH")])
        self.temp.refresh_from_db()
        self.assertEqual(self.temp.alert_state, "HIGH")

        # chu kỳ sau vẫn nóng → không đổi → không có lệnh LED nào
        _, changes = update_alert_states(self.record({**FULL, "temperature": 33.5},
                                                     at=timezone.now() + timedelta(seconds=2)))
        self.assertEqual(changes, [])

    def test_threshold_edit_takes_effect_next_cycle_without_restart(self):
        update_alert_states(self.record({**FULL, "temperature": 33}))
        SensorDevice.objects.filter(pk=self.temp.pk).update(alert_high=40)   # như PUT từ Dashboard
        _, changes = update_alert_states(self.record({**FULL, "temperature": 33},
                                                     at=timezone.now() + timedelta(seconds=2)))
        self.assertEqual([(c.sensor.code, c.state) for c in changes], [("room01_temp", None)])


@mock.patch("apps.sensors.views.events.broadcast")
class AlertConfigEndpointTests(SensorTestCase):
    """PUT /api/sensors/devices/{id}/alert."""

    def setUp(self):
        super().setUp()
        self.temp = SensorDevice.objects.get(code="room01_temp")
        self.url = f"/api/sensors/devices/{self.temp.id}/alert"

    def put(self, **body):
        data = {"alert_enabled": True, "alert_low": None, "alert_high": 32, **body}
        return self.client.put(self.url, data, format="json")

    def test_save_records_who_and_broadcasts(self, broadcast):
        self.login_as(self.operator)
        response = self.put()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual((response.data["alert_enabled"], response.data["alert_low"],
                          response.data["alert_high"]), (True, None, 32.0))
        self.assertEqual(response.data["alert_updated_by"],
                         {"id": self.operator.id, "full_name": self.operator.full_name})
        self.assertIsNotNone(response.data["alert_updated_at"])

        event = broadcast.call_args.args[0]
        self.assertEqual(event["type"], "sensor.alert")
        self.assertEqual(event["sensor"]["alert_high"], 32.0)

        catalog = self.client.get("/api/sensors/devices").data
        self.assertEqual(catalog[0]["alert_high"], 32.0)

    def test_does_not_touch_alert_state(self, broadcast):
        SensorDevice.objects.filter(pk=self.temp.pk).update(alert_state="HIGH")
        self.put(alert_enabled=False)
        self.temp.refresh_from_db()
        self.assertEqual(self.temp.alert_state, "HIGH")    # worker mới được xoá — để còn gửi lệnh tắt LED

    def test_low_not_below_high(self, broadcast):
        error = self.assertError(self.put(alert_low=30, alert_high=30), 400, "VALIDATION_ERROR")
        self.assertIn("alert_high", error["details"])
        broadcast.assert_not_called()

    def test_outside_valid_range(self, broadcast):                    # BR-02: −10 … 60 °C
        error = self.assertError(self.put(alert_high=61), 400, "VALIDATION_ERROR")
        self.assertIn("alert_high", error["details"])
        error = self.assertError(self.put(alert_low=-11), 400, "VALIDATION_ERROR")
        self.assertIn("alert_low", error["details"])

    def test_enabled_needs_one_threshold(self, broadcast):
        error = self.assertError(self.put(alert_high=None), 400, "VALIDATION_ERROR")
        self.assertIn("non_field_errors", error["details"])
        # tắt cảnh báo thì để trống cả hai được
        self.assertEqual(self.put(alert_enabled=False, alert_high=None).status_code, 200)

    def test_missing_field_is_400(self, broadcast):
        response = self.client.put(self.url, {"alert_enabled": True}, format="json")
        self.assertError(response, 400, "VALIDATION_ERROR")

    def test_unknown_or_inactive_sensor_is_404(self, broadcast):
        self.assertError(self.client.put("/api/sensors/devices/999/alert",
                                         {"alert_enabled": False, "alert_low": None,
                                          "alert_high": None}, format="json"), 404, "NOT_FOUND")
        SensorDevice.objects.filter(pk=self.temp.pk).update(is_active=False)
        self.assertError(self.put(), 404, "NOT_FOUND")

    def test_requires_token(self, broadcast):
        self.logout()
        self.assertError(self.put(), 401, "UNAUTHENTICATED")
