"""Logic nghiệp vụ của cảm biến — dùng chung cho API view (đọc) và MQTT worker (ghi).

| Hàm                 | Ai gọi                         | Đặc tả                          |
|---------------------|--------------------------------|---------------------------------|
| `record_cycle()`    | mqtt_worker, topic data_sensors | 04-Database.md §6.4, §7.1; UC-07 |
| `latest_readings()` | GET /api/sensors/latest        | 05-API.md §4.1                  |
| `chart_cycles()`    | GET /api/sensors/chart         | 05-API.md §4.2                  |
"""
import logging
import math
from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from .models import SensorData, SensorDevice

logger = logging.getLogger(__name__)

DEFAULT_NODE_ID = "esp8266_room01"

# Tên trường trong payload MQTT → đại lượng đo (04-Database.md §7.1).
# Thêm cảm biến loại mới: thêm một dòng ở đây + một dòng trong bảng danh mục.
FIELD_TO_METRIC = {
    "temperature": SensorDevice.MetricType.TEMPERATURE,
    "humidity": SensorDevice.MetricType.HUMIDITY,
    "light": SensorDevice.MetricType.LIGHT,
}

# Trường có trong payload nhưng không phải số đo. `timestamp` bị bỏ qua có chủ đích:
# ESP8266 không có đồng hồ thời gian thực, recorded_at do backend sinh (04-Database.md §2.1).
NON_METRIC_FIELDS = {"device_id", "timestamp"}


def metric_key(metric_type):
    """`"TEMPERATURE"` → `"temperature"` — khóa dùng trong biểu đồ và sự kiện sensor.data."""
    return metric_type.lower()


def empty_metrics():
    """`{"temperature": None, "humidity": None, "light": None}` — cảm biến thiếu số đo là null."""
    return {metric_key(m): None for m in SensorDevice.MetricType.values}


# ---------------------------------------------------------------------------
# Ghi một chu kỳ số đo (MQTT worker)
# ---------------------------------------------------------------------------

class SensorCatalog:
    """Danh mục cảm biến nạp vào bộ nhớ MỘT lần lúc worker khởi động.

    Tra theo cặp (node_id, metric_type) — duy nhất nhờ ràng buộc
    `sensordevice_node_metric_unique`. Hệ quả vận hành: sửa ngưỡng hoặc thêm cảm biến
    thì phải khởi động lại mqtt_worker (04-Database.md §7.1).
    """

    def __init__(self, sensors):
        self._by_key = {(s.node_id, s.metric_type): s for s in sensors}
        self._warned = set()

    @classmethod
    def load(cls):
        return cls(SensorDevice.objects.filter(is_active=True))

    def __len__(self):
        return len(self._by_key)

    def find(self, node_id, field_name):
        metric = FIELD_TO_METRIC.get(field_name)
        sensor = self._by_key.get((node_id, metric)) if metric else None
        if sensor is None and (node_id, field_name) not in self._warned:
            # UC-07 E5 — chỉ ghi log MỘT lần, không thì 2 giây lại một dòng log giống hệt
            self._warned.add((node_id, field_name))
            logger.warning("Bỏ qua trường '%s' của node '%s': không có cảm biến tương ứng "
                           "trong danh mục", field_name, node_id)
        return sensor


@dataclass
class SensorCycle:
    """Kết quả ghi một chu kỳ — worker dùng để phát sự kiện sensor.data."""

    node_id: str
    recorded_at: datetime
    readings: list

    def values_by_metric(self):
        values = empty_metrics()
        for reading in self.readings:
            values[metric_key(reading.sensor.metric_type)] = reading.value
        return values


def record_cycle(payload, catalog):
    """Tách một message `data_sensors` thành tối đa 3 bản ghi, ghi bằng MỘT câu INSERT.

    - BR-11: cả chu kỳ dùng chung MỘT `recorded_at`, tính một lần ở đây. Không dùng
      `auto_now_add` — nó gọi now() riêng cho từng dòng, lệch vài micro-giây.
    - UC-07 A2: trường vắng mặt hoặc null → không ghi dòng cho cảm biến đó.
    - UC-07 E3: số đo ngoài ngưỡng BR-02 → loại ĐÚNG số đo đó, các số đo khác vẫn lưu.
    """
    node_id = payload.get("device_id") or DEFAULT_NODE_ID
    recorded_at = timezone.now()
    readings = []

    for field_name, raw in payload.items():
        if field_name in NON_METRIC_FIELDS:
            continue
        sensor = catalog.find(node_id, field_name)
        if sensor is None or raw is None:
            continue
        value = _as_number(raw)
        if value is None:
            logger.warning("Loại số đo %s=%r: không phải số", sensor.code, raw)
            continue
        if not sensor.accepts(value):
            logger.warning("Loại số đo %s=%s: ngoài ngưỡng hợp lệ [%s, %s] (BR-02)",
                           sensor.code, value, sensor.min_value, sensor.max_value)
            continue
        readings.append(SensorData(sensor=sensor, value=value, recorded_at=recorded_at))

    if readings:
        SensorData.objects.bulk_create(readings)
    return SensorCycle(node_id=node_id, recorded_at=recorded_at, readings=readings)


def _as_number(raw):
    """Số thực hữu hạn, hoặc None nếu không phải số (chuỗi, true/false, NaN…)."""
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    value = float(raw)
    return value if math.isfinite(value) else None


# ---------------------------------------------------------------------------
# Truy vấn cho Dashboard (API)
# ---------------------------------------------------------------------------

def latest_readings():
    """Số đo mới nhất của TỪNG cảm biến. Cảm biến chưa có số đo nào thì không có mặt.

    `.distinct("sensor_id")` là DISTINCT ON của PostgreSQL — order_by phải bắt đầu bằng
    đúng trường đó. Dùng chỉ mục `sensordata_sensor_time_unique`.
    """
    return (SensorData.objects
            .filter(sensor__is_active=True)
            .select_related("sensor")
            .order_by("sensor_id", "-recorded_at")
            .distinct("sensor_id"))


def chart_cycles(limit):
    """`limit` chu kỳ gần nhất, xoay thành `[{recorded_at, temperature, humidity, light}]`.

    Phải chốt TẬP MỐC THỜI GIAN trước rồi mới lấy số đo. Viết `LIMIT limit*3` là sai:
    chỉ cần một cảm biến lỗi vài chu kỳ là số dòng không còn phủ đúng `limit` mốc.
    Mốc nào thiếu số đo thì trường đó là None → biểu đồ đứt nét đúng chỗ (UC-07 A2).
    Trả về theo thời gian TĂNG dần vì Recharts vẽ theo thứ tự phần tử.
    """
    active = SensorData.objects.filter(sensor__is_active=True)
    stamps = list(active.order_by("-recorded_at")
                        .values_list("recorded_at", flat=True)
                        .distinct()[:limit])

    points = {stamp: {"recorded_at": stamp, **empty_metrics()} for stamp in sorted(stamps)}
    rows = active.filter(recorded_at__in=stamps).values_list(
        "recorded_at", "sensor__metric_type", "value")
    for stamp, metric_type, value in rows:
        points[stamp][metric_key(metric_type)] = value
    return list(points.values())
