from django.contrib import admin

from .models import SensorData, SensorDevice


@admin.register(SensorDevice)
class SensorDeviceAdmin(admin.ModelAdmin):
    list_display = ["id", "code", "name", "metric_type", "unit", "node_id",
                    "min_value", "max_value", "is_active"]
    list_filter = ["metric_type", "node_id", "is_active"]


@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ["id", "sensor", "value", "recorded_at"]
    list_filter = ["sensor"]
    list_select_related = ["sensor"]
    date_hierarchy = "recorded_at"
    # Số đo do MQTT worker ghi — không cho sửa tay trên trang admin
    readonly_fields = ["sensor", "value", "recorded_at"]
