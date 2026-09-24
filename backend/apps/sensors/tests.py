"""Cảm biến: ghi một chu kỳ (UC-07) và 4 endpoint /api/sensors — ca A-00 → A-07f."""
from datetime import timedelta
from unittest import mock

from django.utils import timezone

from apps.core.testing import LoggedInAPITestCase

from .models import SensorData
from .services import SensorCatalog, record_cycle

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
        self.assertEqual(set(response.data[0]), {"id", "code", "name", "metric_type", "unit", "node_id"})

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
