"""Bảng sensors_sensordevice và sensors_sensordata — 04-Database.md §4.2, §4.3, §8.2."""
from django.db import models
from django.utils import timezone


class SensorDevice(models.Model):
    """Danh mục cảm biến: đo đại lượng nào, đơn vị gì, ngưỡng hợp lệ tới đâu."""

    class MetricType(models.TextChoices):
        TEMPERATURE = "TEMPERATURE", "Nhiệt độ"
        HUMIDITY = "HUMIDITY", "Độ ẩm"
        LIGHT = "LIGHT", "Ánh sáng"

    code = models.CharField(max_length=30, unique=True, verbose_name="Mã cảm biến")
    name = models.CharField(max_length=100, verbose_name="Tên hiển thị")
    metric_type = models.CharField(
        max_length=20, choices=MetricType.choices, verbose_name="Đại lượng đo"
    )
    unit = models.CharField(max_length=10, verbose_name="Đơn vị")
    hardware_model = models.CharField(max_length=50, blank=True, verbose_name="Model phần cứng")
    node_id = models.CharField(max_length=50, default="esp8266_room01", verbose_name="Mã bo mạch")
    # BR-02 — ngưỡng là dữ liệu cấu hình; sửa ở đây rồi khởi động lại mqtt_worker
    min_value = models.FloatField(verbose_name="Ngưỡng dưới hợp lệ")
    max_value = models.FloatField(verbose_name="Ngưỡng trên hợp lệ")
    is_active = models.BooleanField(default=True, verbose_name="Đang sử dụng")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cảm biến"
        verbose_name_plural = "Cảm biến"
        ordering = ["id"]
        constraints = [
            # Mỗi bo mạch chỉ một cảm biến cho mỗi đại lượng → worker ánh xạ được
            # trường `temperature` của payload sang đúng một dòng (04-Database.md §7.1)
            models.UniqueConstraint(
                fields=["node_id", "metric_type"], name="sensordevice_node_metric_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(metric_type__in=["TEMPERATURE", "HUMIDITY", "LIGHT"]),
                name="sensordevice_metric_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(min_value__lt=models.F("max_value")),
                name="sensordevice_range_valid",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def accepts(self, value):
        """BR-02: số đo có nằm trong ngưỡng hợp lệ của CHÍNH cảm biến này không."""
        return self.min_value <= value <= self.max_value


class SensorData(models.Model):
    """Một số đo của MỘT cảm biến tại MỘT thời điểm.

    Một message `data_sensors` sinh ra tới ba bản ghi ở đây, cả ba mang CÙNG một
    `recorded_at` (BR-11) — xem `services.record_cycle()`.
    """

    sensor = models.ForeignKey(
        SensorDevice,
        on_delete=models.PROTECT,       # NFR-06 — không mất số liệu
        related_name="readings",
        db_index=False,                 # đã có UNIQUE(sensor, recorded_at) — §5.2
        verbose_name="Cảm biến",
    )
    value = models.FloatField(verbose_name="Giá trị đo")
    recorded_at = models.DateTimeField(
        default=timezone.now,           # KHÔNG dùng auto_now_add — 04-Database.md §2.2
        verbose_name="Thời điểm ghi nhận",
    )

    class Meta:
        verbose_name = "Số đo cảm biến"
        verbose_name_plural = "Số đo cảm biến"
        # BR-09 + cột phá hoà: 3 dòng cùng chu kỳ trùng recorded_at, sensor_id chốt thứ tự
        # Nhiệt độ → Độ ẩm → Ánh sáng (04-Database.md §5.2)
        ordering = ["-recorded_at", "sensor_id"]
        indexes = [
            models.Index(fields=["-recorded_at", "sensor_id"], name="idx_sensordata_recorded_desc"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["sensor", "recorded_at"], name="sensordata_sensor_time_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(value__gte=-1000, value__lte=100000),
                name="sensordata_value_sane",   # lưới an toàn thô, KHÔNG phải BR-02 (§2.4)
            ),
        ]

    def __str__(self):
        return f"{self.recorded_at:%d/%m/%Y %H:%M:%S} — {self.sensor.code} = {self.value}"
