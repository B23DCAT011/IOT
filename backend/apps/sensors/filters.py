"""Tham số lọc của GET /api/sensors — 05-API.md §4.3, §7.3; UC-04."""
from django import forms
from django_filters import rest_framework as filters

from apps.core.filters import RangeCheckForm

from .models import SensorData


class SensorDataFilterForm(RangeCheckForm):
    range_pairs = [
        ("recorded_at__gte", "recorded_at__lte"),
        ("value__gte", "value__lte"),
    ]

    def clean(self):
        cleaned = super().clean()
        # UC-04 E4 — khoảng giá trị chỉ có nghĩa khi đã chọn MỘT cảm biến: ba đại lượng
        # khác đơn vị, "từ 28 tới 30" áp cho cả bảng sẽ gộp 28 °C với 28 lux.
        if not cleaned.get("sensor"):
            for field in ("value__gte", "value__lte"):
                if cleaned.get(field) is not None:
                    self.add_error(field, forms.ValidationError(
                        "Phải chọn một cảm biến trước khi lọc theo khoảng giá trị.",
                        code="sensor_required",
                    ))
        return cleaned


class SensorDataFilter(filters.FilterSet):
    # Lọc theo MÃ cảm biến (`?sensor=room01_temp`), không theo id — đọc được, và không
    # đổi khi chạy lại migration ở máy khác.
    sensor = filters.CharFilter(field_name="sensor__code", lookup_expr="exact")
    node = filters.CharFilter(field_name="sensor__node_id", lookup_expr="exact")

    class Meta:
        model = SensorData
        form = SensorDataFilterForm
        # Dạng dict → django-filter tự sinh `recorded_at__gte`, `recorded_at__lte`, `value__gte`, `value__lte`
        fields = {
            "recorded_at": ["gte", "lte"],
            "value": ["gte", "lte"],
        }
