from django.contrib import admin

from .models import ActionHistory, Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["id", "code", "name", "device_type", "node_id", "gpio_pin",
                    "current_state", "is_active", "updated_at"]
    list_filter = ["device_type", "node_id", "is_active"]
    # current_state chỉ được đổi bởi mqtt_worker khi thiết bị xác nhận (04-Database.md §4.4)
    readonly_fields = ["current_state"]


@admin.register(ActionHistory)
class ActionHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "device", "action", "user", "status", "created_at",
                    "responded_at", "latency_ms"]
    list_filter = ["status", "action", "device"]
    list_select_related = ["device", "user"]
    search_fields = ["request_id", "error_message"]
    readonly_fields = ["request_id", "created_at"]
