"""Mô tả hình dạng lỗi cho Swagger — drf-spectacular không tự biết (05-API.md §8.1)."""
from rest_framework import serializers


class ErrorBodySerializer(serializers.Serializer):
    code = serializers.CharField(help_text="Một trong 9 mã ở 05-API.md §2.7")
    message = serializers.CharField()
    details = serializers.JSONField(allow_null=True)


class ErrorSerializer(serializers.Serializer):
    error = ErrorBodySerializer()


def error_responses(*status_codes):
    """`error_responses(400, 404)` → `{400: ErrorSerializer, 404: ErrorSerializer}`."""
    return {code: ErrorSerializer for code in status_codes}
