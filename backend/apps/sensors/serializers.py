"""Hình dạng JSON của nhóm /api/sensors — 05-API.md §4.0 → §4.3."""
from rest_framework import serializers

from apps.users.serializers import UserBriefSerializer

from .models import SensorData, SensorDevice


class SensorDeviceSerializer(serializers.ModelSerializer):
    """GET /api/sensors/devices — kèm cấu hình cảnh báo để Dashboard vẽ ô chỉnh ngưỡng.

    `min_value`/`max_value` (ngưỡng hợp lệ, BR-02) trả về để giao diện ghi "Cho phép: …"
    và chặn nhập ngưỡng cảnh báo nằm ngoài khoảng đó — người dùng KHÔNG sửa được hai cột này.
    """

    alert_updated_by = UserBriefSerializer(allow_null=True, read_only=True)

    class Meta:
        model = SensorDevice
        fields = ["id", "code", "name", "metric_type", "unit", "node_id",
                  "min_value", "max_value",
                  "alert_enabled", "alert_low", "alert_high", "alert_state",
                  "alert_device",            # id thiết bị đèn cảnh báo trong GET /api/devices
                  "alert_updated_at", "alert_updated_by"]


class AlertConfigSerializer(serializers.Serializer):
    """Thân của PUT /api/sensors/devices/{id}/alert. Cần `context["sensor"]` để biết ngưỡng hợp lệ.

    Gửi đủ cả ba trường (PUT thay toàn bộ cấu hình); ô bỏ trống gửi `null` = không cảnh báo chiều đó.
    """

    alert_enabled = serializers.BooleanField()
    alert_low = serializers.FloatField(allow_null=True)
    alert_high = serializers.FloatField(allow_null=True)

    def _check_in_range(self, value):
        sensor = self.context["sensor"]
        if value is not None and not sensor.accepts(value):
            raise serializers.ValidationError(
                f"Phải nằm trong khoảng hợp lệ {sensor.min_value:g} … {sensor.max_value:g} {sensor.unit}.")
        return value

    def validate_alert_low(self, value):
        return self._check_in_range(value)

    def validate_alert_high(self, value):
        return self._check_in_range(value)

    def validate(self, attrs):
        low, high = attrs["alert_low"], attrs["alert_high"]
        if low is not None and high is not None and low >= high:
            raise serializers.ValidationError({"alert_high": "Ngưỡng trên phải lớn hơn ngưỡng dưới."})
        if attrs["alert_enabled"] and low is None and high is None:
            raise serializers.ValidationError(
                {"non_field_errors": ["Bật cảnh báo thì phải đặt ít nhất một ngưỡng."]})
        return attrs


class SensorBriefSerializer(serializers.ModelSerializer):
    """Cảm biến rút gọn, lồng trong mỗi số đo."""

    class Meta:
        model = SensorDevice
        fields = ["id", "code", "name", "unit"]


class LatestReadingSerializer(serializers.ModelSerializer):
    """Một phần tử của GET /api/sensors/latest (§4.1)."""

    sensor = SensorBriefSerializer()

    class Meta:
        model = SensorData
        fields = ["sensor", "value", "recorded_at"]


class SensorReadingSerializer(LatestReadingSerializer):
    """Một dòng của bảng GET /api/sensors (§4.3) — thêm `id`."""

    class Meta(LatestReadingSerializer.Meta):
        fields = ["id", *LatestReadingSerializer.Meta.fields]


class ChartPointSerializer(serializers.Serializer):
    """Một CHU KỲ trên biểu đồ (§4.2). Khóa là metric_type viết thường; thiếu số đo → null."""

    recorded_at = serializers.DateTimeField()
    temperature = serializers.FloatField(allow_null=True)
    humidity = serializers.FloatField(allow_null=True)
    light = serializers.FloatField(allow_null=True)


class ChartQuerySerializer(serializers.Serializer):
    """Tham số `limit` của /api/sensors/chart: sai kiểu → 400, lớn hơn 100 → tự hạ về 100."""

    MAX_LIMIT = 100
    limit = serializers.IntegerField(min_value=1, default=20)   # BR-10

    def validate_limit(self, value):
        return min(value, self.MAX_LIMIT)
