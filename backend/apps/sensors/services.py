"""Logic nghiệp vụ của cảm biến — dùng chung cho API view (đọc) và MQTT worker (ghi).

| Hàm                 | Ai gọi                         | Đặc tả                          |
|---------------------|--------------------------------|---------------------------------|
| `record_cycle()`    | mqtt_worker, topic data_sensors | 04-Database.md §6.4, §7.1; UC-07 |
| `latest_readings()` | GET /api/sensors/latest        | 05-API.md §4.1                  |
| `chart_cycles()`    | GET /api/sensors/chart         | 05-API.md §4.2                  |
| `update_alert_states()` | mqtt_worker, sau `record_cycle()` | cảnh báo vượt ngưỡng      |
| `led_action()` / `sensor_for_alert_led()` | mqtt_worker | lệnh cho đèn cảnh báo        |
| `save_alert_config()`   | PUT /api/sensors/devices/{id}/alert | cảnh báo vượt ngưỡng    |
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


# ---------------------------------------------------------------------------
# Cảnh báo vượt ngưỡng (MQTT worker ghi trạng thái, API ghi cấu hình)
# ---------------------------------------------------------------------------

# Vùng đệm: đã cảnh báo thì phải về hẳn bên trong ngưỡng một khoảng này mới thôi. Không có
# nó, nhiệt độ dao động 32,0 ↔ 32,1 quanh ngưỡng 32 sẽ làm LED và thẻ bật/tắt mỗi 2 giây.
ALERT_HYSTERESIS = {
    SensorDevice.MetricType.TEMPERATURE: 0.5,   # °C
    SensorDevice.MetricType.HUMIDITY: 2.0,      # %
    SensorDevice.MetricType.LIGHT: 20.0,        # lux
}

HIGH = SensorDevice.AlertState.HIGH
LOW = SensorDevice.AlertState.LOW


def next_alert_state(sensor, value, current):
    """Trạng thái cảnh báo sau khi nhận số đo `value`. `current` là trạng thái trước đó.

    Vượt hẳn ngưỡng (> trên, < dưới) thì cảnh báo ngay; đang cảnh báo thì chỉ thôi khi đã
    về bên trong ngưỡng quá vùng đệm. `value` là None (chu kỳ này không đo được) → giữ nguyên.
    """
    if not sensor.alert_enabled:
        return None
    if value is None:
        return current
    high, low = sensor.alert_high, sensor.alert_low
    band = ALERT_HYSTERESIS.get(sensor.metric_type, 0)

    if high is not None and value > high:
        return HIGH
    if low is not None and value < low:
        return LOW
    if current == HIGH and high is not None and value > high - band:
        return HIGH
    if current == LOW and low is not None and value < low + band:
        return LOW
    return None


@dataclass
class AlertChange:
    """Một cảm biến vừa đổi trạng thái cảnh báo — worker gửi lệnh cho LED tương ứng."""

    sensor: SensorDevice
    state: str | None


def update_alert_states(cycle):
    """So số đo của chu kỳ với ngưỡng cảnh báo, ghi lại cảm biến nào ĐỔI trạng thái.

    Đọc lại ngưỡng từ CSDL mỗi chu kỳ (3 dòng, một truy vấn) thay vì dùng danh mục nạp sẵn
    của worker: người dùng sửa ngưỡng trên Dashboard thì chậm nhất một chu kỳ sau đã có hiệu
    lực, không phải khởi động lại worker.

    Trả `(alerts, changes)`: `alerts` là trạng thái của MỌI cảm biến trong node theo khóa
    `temperature`/`humidity`/`light` (đi kèm sự kiện sensor.data), `changes` là danh sách
    `AlertChange` cần báo xuống mạch.
    """
    values = {reading.sensor_id: reading.value for reading in cycle.readings}
    alerts = empty_metrics()
    changes = []
    sensors = (SensorDevice.objects.filter(is_active=True, node_id=cycle.node_id)
               .select_related("alert_device"))
    for sensor in sensors:
        state = next_alert_state(sensor, values.get(sensor.id), sensor.alert_state)
        if state != sensor.alert_state:
            sensor.alert_state = state
            sensor.save(update_fields=["alert_state"])
            changes.append(AlertChange(sensor=sensor, state=state))
            logger.info("Cảnh báo %s: %s (giá trị %s)", sensor.code, state or "hết",
                        values.get(sensor.id))
        alerts[metric_key(sensor.metric_type)] = state
    return alerts, changes


def led_action(sensor):
    """Đèn cảnh báo của cảm biến phải ở trạng thái nào: "ON" (nháy) khi đang vượt ngưỡng, còn lại "OFF"."""
    return "ON" if sensor.alert_enabled and sensor.alert_state else "OFF"


def sensor_for_alert_led(device_code):
    """Cảm biến mà đèn cảnh báo mang mã `device_code` phụ trách, hoặc None nếu không phải đèn cảnh báo."""
    return (SensorDevice.objects.select_related("alert_device")
            .filter(is_active=True, alert_device__code=device_code).first())


def save_alert_config(sensor, *, alert_enabled, alert_low, alert_high, user):
    """Lưu ngưỡng cảnh báo do người dùng nhập. KHÔNG đụng `alert_state`.

    Trạng thái cảnh báo và lệnh cho LED chỉ do worker sinh ra, ở chu kỳ kế tiếp (≤ 2 giây).
    Nếu ở đây tự xoá `alert_state` khi tắt cảnh báo, worker sẽ thấy "trước đã là None" và
    không bao giờ gửi lệnh tắt — LED trên mạch nháy mãi.
    """
    sensor.alert_enabled = alert_enabled
    sensor.alert_low = alert_low
    sensor.alert_high = alert_high
    sensor.alert_updated_at = timezone.now()
    sensor.alert_updated_by = user
    sensor.save(update_fields=["alert_enabled", "alert_low", "alert_high",
                               "alert_updated_at", "alert_updated_by", "updated_at"])
    return sensor


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
