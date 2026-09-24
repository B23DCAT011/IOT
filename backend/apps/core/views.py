"""GET /api/profile — UC-06, 05-API.md §4.7."""
from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .schema import error_responses


def _nullable_fields(*names):
    return {name: serializers.CharField(allow_null=True) for name in names}


ProfileSchema = inline_serializer("Profile", {
    "student": inline_serializer("ProfileStudent", _nullable_fields(
        "full_name", "student_id", "class_name", "email", "avatar_url")),
    "project": inline_serializer("ProfileProject", _nullable_fields(
        "title", "subject", "supervisor")),
    "links": inline_serializer("ProfileLinks", _nullable_fields(
        "github", "report_pdf", "figma", "api_docs")),
})


class ProfileView(APIView):
    """Thông tin sinh viên và liên kết bàn giao — đọc từ `.env`, không có bảng CSDL.

    Biến để trống ⇒ `null`, Frontend hiện nút vô hiệu "Đang cập nhật" (UC-06 E1).
    """

    @extend_schema(responses={200: ProfileSchema, **error_responses(401)}, tags=["Profile"])
    def get(self, request):
        return Response(settings.PROFILE)
