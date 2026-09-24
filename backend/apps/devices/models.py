"""Bảng devices_device và devices_actionhistory — 04-Database.md §4.4, §4.5, §8.3."""
import uuid

from django.conf import settings
from django.db import models


class Device(models.Model):
    """Thiết bị chấp hành bật/tắt được từ giao diện (đèn, quạt)."""

    class DeviceType(models.TextChoices):
        LIGHT = "LIGHT", "Đèn"
        FAN = "FAN", "Quạt"
        OTHER = "OTHER", "Khác"

    class State(models.TextChoices):
        ON = "ON", "Bật"
        OFF = "OFF", "Tắt"

    # `code` là chuỗi firmware so sánh (`if (device == "room01_lamp")`) — trường `device` của MQTT
    code = models.CharField(max_length=30, unique=True, verbose_name="Mã thiết bị")
    name = models.CharField(max_length=100, verbose_name="Tên hiển thị")
    device_type = models.CharField(
        max_length=20, choices=DeviceType.choices, default=DeviceType.OTHER,
        verbose_name="Loại thiết bị",
    )
    node_id = models.CharField(max_length=50, default="esp8266_room01", verbose_name="Mã bo mạch")
    # KHÔNG unique=True — chỉ duy nhất theo cặp (node_id, gpio_pin), §4.4a
    gpio_pin = models.CharField(max_length=10, verbose_name="Chân GPIO")
    # Trạng thái vật lý ĐÃ XÁC NHẬN — chỉ đổi khi lệnh SUCCESS (services.confirm_command)
    current_state = models.CharField(
        max_length=10, choices=State.choices, default=State.OFF,
        verbose_name="Trạng thái hiện tại",
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang sử dụng")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Thiết bị"
        verbose_name_plural = "Thiết bị"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["node_id", "gpio_pin"], name="device_node_gpio_unique"),
            models.CheckConstraint(
                condition=models.Q(current_state__in=["ON", "OFF"]), name="device_state_valid"
            ),
            models.CheckConstraint(
                condition=models.Q(device_type__in=["LIGHT", "FAN", "OTHER"]),
                name="device_type_valid",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class ActionHistory(models.Model):
    """Một lần điều khiển thiết bị: sinh PENDING khi API nhận lệnh, kết thúc ở SUCCESS/FAILED (BR-05)."""

    class Action(models.TextChoices):
        ON = "ON", "Bật"
        OFF = "OFF", "Tắt"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Đang chờ"
        SUCCESS = "SUCCESS", "Thành công"
        FAILED = "FAILED", "Thất bại"

    device = models.ForeignKey(
        Device, on_delete=models.PROTECT,        # NFR-06: không mất lịch sử
        related_name="actions", verbose_name="Thiết bị",
    )
    # NULL = lệnh không đi qua API (seed, admin, shell) — BR-12. Giao diện hiện "—".
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="actions", verbose_name="Người thao tác",
    )
    request_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, verbose_name="Mã yêu cầu",   # BR-06
    )
    action = models.CharField(max_length=10, choices=Action.choices, verbose_name="Hành động")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True,
        verbose_name="Trạng thái",
    )
    error_message = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Lý do thất bại"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm gửi lệnh")
    # Thời điểm lệnh KẾT THÚC: nhận device_respond, hoặc lúc bị đánh hết giờ (§4.5)
    responded_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Thời điểm kết thúc lệnh"
    )

    class Meta:
        verbose_name = "Lịch sử thao tác"
        verbose_name_plural = "Lịch sử thao tác"
        ordering = ["-created_at"]                                   # BR-09
        indexes = [
            models.Index(fields=["-created_at"], name="idx_action_created_desc"),
            models.Index(fields=["device", "-created_at"], name="idx_action_dev_created"),
            # Chỉ chứa vài dòng PENDING — phục vụ vòng quét timeout và kiểm tra bận (409)
            models.Index(
                fields=["created_at"], name="idx_action_pending",
                condition=models.Q(status="PENDING"),
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(action__in=["ON", "OFF"]), name="action_action_valid"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["PENDING", "SUCCESS", "FAILED"]),
                name="action_status_valid",
            ),
            # PENDING ⇔ chưa có responded_at — chặn lỗi quên đặt mốc kết thúc
            models.CheckConstraint(
                condition=(
                    models.Q(status="PENDING", responded_at__isnull=True)
                    | ~models.Q(status="PENDING") & models.Q(responded_at__isnull=False)
                ),
                name="action_responded_consistency",
            ),
        ]

    @property
    def latency_ms(self):
        """Suy ra từ responded_at − created_at, không lưu thành cột (3NF)."""
        if self.responded_at is None:
            return None
        return int((self.responded_at - self.created_at).total_seconds() * 1000)

    def __str__(self):
        return f"#{self.pk} {self.device.code} {self.action} — {self.status}"
