"""GET /api/profile — UC-06, 05-API.md §4.7."""
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView


class ProfileView(APIView):
    """Thông tin sinh viên và liên kết bàn giao — đọc từ `.env`, không có bảng CSDL.

    Biến để trống ⇒ `null`, Frontend hiện nút vô hiệu "Đang cập nhật" (UC-06 E1).
    """

    def get(self, request):
        return Response(settings.PROFILE)
