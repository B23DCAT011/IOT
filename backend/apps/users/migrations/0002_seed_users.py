"""Hai tài khoản khởi tạo — 04-Database.md §10.2.

Mật khẩu mặc định trùng với frontend/README.md để đổi từ MSW sang backend thật không vướng.
ĐỔI trước khi demo:  python manage.py changepassword admin
"""
from django.contrib.auth.hashers import make_password
from django.db import migrations

DEFAULT_PASSWORD = "doi-mat-khau-nay"

SEED = [
    {"username": "admin", "full_name": "Lưu Đức Anh", "role": "ADMIN",
     "is_staff": True, "is_superuser": True},
    {"username": "operator", "full_name": "Người vận hành", "role": "OPERATOR",
     "is_staff": False, "is_superuser": False},
]


def create_users(apps, schema_editor):
    User = apps.get_model("users", "User")
    for item in SEED:
        # Model lịch sử trong migration không có create_user() → băm bằng make_password().
        # Gán chuỗi thô vào cột password thì mọi lần đăng nhập đều thất bại.
        User.objects.get_or_create(
            username=item["username"],
            defaults={**item, "password": make_password(DEFAULT_PASSWORD)},
        )


def remove_users(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(username__in=[i["username"] for i in SEED]).delete()


class Migration(migrations.Migration):
    dependencies = [("users", "0001_initial")]
    operations = [migrations.RunPython(create_users, remove_users)]
