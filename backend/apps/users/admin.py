from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["id", "username", "full_name", "role", "is_active", "last_login"]
    list_filter = ["role", "is_active"]
    search_fields = ["username", "full_name"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Thông tin dự án", {"fields": ["full_name", "role"]}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Thông tin dự án", {"fields": ["full_name", "role"]}),
    )
