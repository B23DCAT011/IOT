"""Nhóm endpoint /api/devices và /api/actions — 05-API.md §4.4 → §4.6.

    GET  /api/devices                danh sách thiết bị kèm trạng thái  (UC-01)
    GET  /api/devices/{id}           một thiết bị                       (chỉ để thử bằng Postman)
    POST /api/devices/{id}/control   gửi lệnh bật/tắt → 202             (UC-02)
    GET  /api/actions                bảng lịch sử thao tác              (UC-05, UC-04)
    GET  /api/actions/{id}           một bản ghi lịch sử
"""
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.schema import error_responses

from . import services
from .filters import ActionHistoryFilter
from .models import ActionHistory, Device
from .serializers import (
    ActionHistorySerializer,
    ControlAcceptedSerializer,
    ControlRequestSerializer,
    DeviceSerializer,
)


@extend_schema_view(
    list=extend_schema(responses={200: DeviceSerializer(many=True), **error_responses(401)}),
    retrieve=extend_schema(responses={200: DeviceSerializer, **error_responses(401, 404)}),
)
@extend_schema(tags=["Devices"])
class DeviceViewSet(ReadOnlyModelViewSet):
    # Thiết bị đã tháo (is_active=false) coi như không tồn tại: không có trong danh sách,
    # điều khiển thì 404 — nhất quán giữa danh sách và thao tác (05-API.md §4.5).
    queryset = Device.objects.filter(is_active=True)
    serializer_class = DeviceSerializer
    pagination_class = None       # bắt buộc: PAGE_SIZE toàn cục sẽ bọc mảng trong {count, results}
    filter_backends = []

    @extend_schema(
        request=ControlRequestSerializer,
        responses={202: ControlAcceptedSerializer, **error_responses(400, 401, 404, 409, 503)},
        examples=[OpenApiExample("Bật đèn", value={"action": "ON"}, request_only=True)],
    )
    @action(detail=True, methods=["post"], url_path="control")
    def control(self, request, pk=None):
        device = self.get_object()                                   # 404 — UC-02 E3
        body = ControlRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)                          # 400 — UC-02 E4

        # Người thao tác lấy từ token, không từ thân yêu cầu (BR-12, bản 2.1)
        record = services.send_command(device, body.validated_data["action"], request.user)

        # 202 chứ không phải 200: đèn CHƯA sáng — kết quả thật về qua WebSocket device.state
        return Response(ControlAcceptedSerializer(record).data, status=status.HTTP_202_ACCEPTED)


@extend_schema_view(
    list=extend_schema(responses={200: ActionHistorySerializer(many=True),
                                  **error_responses(400, 401, 404)}),
    retrieve=extend_schema(responses={200: ActionHistorySerializer, **error_responses(401, 404)}),
)
@extend_schema(tags=["Actions"])
class ActionHistoryViewSet(ReadOnlyModelViewSet):
    # select_related BẮT BUỘC — thiếu thì 10 dòng thành 21 truy vấn (04-Database.md §11.3)
    queryset = ActionHistory.objects.select_related("device", "user")
    serializer_class = ActionHistorySerializer
    filterset_class = ActionHistoryFilter
    search_fields = ["device__name", "device__code", "user__full_name", "error_message"]
    ordering_fields = ["created_at", "responded_at", "status", "action", "id"]
    ordering = ["-created_at"]                                       # BR-09
    ordering_tiebreak = ["-id"]
