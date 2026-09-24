from rest_framework import serializers

from .models import User


class UserBriefSerializer(serializers.ModelSerializer):
    """Người thao tác rút gọn — lồng trong lịch sử và phản hồi điều khiển (05-API.md §4.5, §4.6)."""

    class Meta:
        model = User
        fields = ["id", "full_name"]


class LoginUserSerializer(serializers.ModelSerializer):
    """Người dùng trả về lúc đăng nhập — thêm `username` và `role` để hiện ở sidebar (§4.8)."""

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "role"]


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    # Mặc định CharField cắt khoảng trắng hai đầu → mật khẩu có dấu cách không bao giờ khớp.
    password = serializers.CharField(trim_whitespace=False)


class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = LoginUserSerializer()
