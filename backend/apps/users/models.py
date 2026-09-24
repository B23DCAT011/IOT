"""Bảng users_user — 04-Database.md §4.1, §8.1."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Người thao tác trên hệ thống.

    Kế thừa AbstractUser để dùng lại băm mật khẩu, trang admin và `is_active`.
    Hai cột `first_name`/`last_name` kế thừa để trống — tên tiếng Việt lưu ở `full_name`.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Quản trị"
        OPERATOR = "OPERATOR", "Người vận hành"
        VIEWER = "VIEWER", "Chỉ xem"

    full_name = models.CharField(max_length=100, blank=True, verbose_name="Họ và tên")
    # Hiện chỉ mang tính mô tả — chưa phân quyền theo vai trò (05-API.md §12 điểm 3b)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.OPERATOR, verbose_name="Vai trò"
    )

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=["ADMIN", "OPERATOR", "VIEWER"]),
                name="user_role_valid",
            ),
        ]

    def __str__(self):
        return self.full_name or self.username
