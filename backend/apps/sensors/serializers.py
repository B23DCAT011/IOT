"""Hình dạng JSON của nhóm /api/sensors — 05-API.md §4.0 → §4.3."""
from rest_framework import serializers

from .models import SensorData, SensorDevice


class SensorDeviceSerializer(serializers.ModelSerializer):
    """GET /api/sensors/devices — KHÔNG trả min_value/max_value (chỉ worker dùng)."""

    class Meta:
        model = SensorDevice
        fields = ["id", "code", "name", "metric_type", "unit", "node_id"]


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
