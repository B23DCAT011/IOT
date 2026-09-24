"""Hình dạng JSON của /api/devices và /api/actions — 05-API.md §4.4 → §4.6."""
from rest_framework import serializers

from apps.users.serializers import UserBriefSerializer

from .models import ActionHistory, Device


class DeviceSerializer(serializers.ModelSerializer):
    """GET /api/devices — không trả `is_active` vì danh sách đã lọc sẵn."""

    class Meta:
        model = Device
        fields = ["id", "code", "name", "device_type", "node_id", "gpio_pin",
                  "current_state", "updated_at"]


class DeviceBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "code", "name"]


class ControlRequestSerializer(serializers.Serializer):
    """Thân POST /api/devices/{id}/control.

    Chỉ khai `action`: `user_id` người gọi gửi kèm bị bỏ qua — người thao tác lấy từ
    token, không giả mạo được (05-API.md §4.5, ca A-11c).
    """

    action = serializers.CharField()

    def validate_action(self, value):
        value = value.strip().upper()          # "on" → "ON"
        if value not in ActionHistory.Action.values:
            raise serializers.ValidationError('Giá trị phải là "ON" hoặc "OFF".')
        return value


class ControlAcceptedSerializer(serializers.ModelSerializer):
    """Phản hồi 202 — lệnh đã tiếp nhận, CHƯA hoàn tất. Kết quả về qua WebSocket."""

    device_id = serializers.IntegerField(source="device.id")
    device = serializers.CharField(source="device.code")
    user = UserBriefSerializer()

    class Meta:
        model = ActionHistory
        fields = ["request_id", "device_id", "device", "action", "user", "status", "created_at"]


class ActionHistorySerializer(serializers.ModelSerializer):
    """Một dòng của GET /api/actions. `user` có thể null (BR-12) — Frontend hiện "—"."""

    device = DeviceBriefSerializer()
    user = UserBriefSerializer(allow_null=True)
    latency_ms = serializers.IntegerField(allow_null=True, read_only=True)

    class Meta:
        model = ActionHistory
        fields = ["id", "device", "action", "user", "status", "error_message", "request_id",
                  "created_at", "responded_at", "latency_ms"]
