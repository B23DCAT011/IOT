"""Nhóm endpoint /api/sensors — 05-API.md §4.0 → §4.3.

    GET /api/sensors            bảng số đo, lọc/sắp xếp/phân trang   (UC-03, UC-04)
    GET /api/sensors/{id}       một số đo                             (chỉ để thử bằng Postman)
    GET /api/sensors/devices    danh mục cảm biến                     (UC-01)
    GET /api/sensors/latest     số đo mới nhất của từng cảm biến      (UC-01)
    GET /api/sensors/chart      N chu kỳ gần nhất cho biểu đồ         (UC-01, BR-10)
    PUT /api/sensors/devices/{id}/alert   sửa ngưỡng cảnh báo         (Dashboard)
"""
import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.schema import error_responses
from apps.realtime import events

from . import services
from .filters import SensorDataFilter
from .models import SensorData, SensorDevice
from .serializers import (
    AlertConfigSerializer,
    ChartPointSerializer,
    ChartQuerySerializer,
    LatestReadingSerializer,
    SensorDeviceSerializer,
    SensorReadingSerializer,
)

logger = logging.getLogger(__name__)

# Ba endpoint phụ không phân trang, không lọc — trả mảng thuần.
PLAIN_ARRAY = {"pagination_class": None, "filter_backends": []}


@extend_schema_view(
    list=extend_schema(responses={200: SensorReadingSerializer(many=True),
                                  **error_responses(400, 401, 404)}),
    retrieve=extend_schema(responses={200: SensorReadingSerializer, **error_responses(401, 404)}),
)
@extend_schema(tags=["Sensors"])
class SensorViewSet(ReadOnlyModelViewSet):
    # select_related BẮT BUỘC: mỗi dòng đọc sensor.code/name/unit, thiếu nó thì
    # 10 dòng thành 11 truy vấn (04-Database.md §11.3).
    queryset = SensorData.objects.select_related("sensor")
    serializer_class = SensorReadingSerializer
    filterset_class = SensorDataFilter
    search_fields = ["sensor__code", "sensor__name"]
    ordering_fields = ["recorded_at", "value", "id"]
    ordering = ["-recorded_at", "sensor_id"]            # BR-09 + BR-11
    ordering_tiebreak = ["sensor_id", "id"]             # xem TiebreakOrderingFilter

    @extend_schema(responses={200: SensorDeviceSerializer(many=True), **error_responses(401)})
    @action(detail=False, url_path="devices", **PLAIN_ARRAY)
    def devices(self, request):
        sensors = SensorDevice.objects.filter(is_active=True).select_related("alert_updated_by")
        return Response(SensorDeviceSerializer(sensors, many=True).data)

    @extend_schema(
        request=AlertConfigSerializer,
        responses={200: SensorDeviceSerializer, **error_responses(400, 401, 404)},
        examples=[OpenApiExample(
            "Cảnh báo khi nóng quá 32 °C",
            value={"alert_enabled": True, "alert_low": None, "alert_high": 32},
            request_only=True,
        )],
    )
    @action(detail=False, methods=["put"], url_path=r"devices/(?P<sensor_id>\d+)/alert",
            **PLAIN_ARRAY)
    def alert(self, request, sensor_id=None):
        """Sửa ngưỡng cảnh báo của một cảm biến. Ai đăng nhập cũng sửa được."""
        sensor = get_object_or_404(SensorDevice.objects.filter(is_active=True), pk=sensor_id)
        body = AlertConfigSerializer(data=request.data, context={"sensor": sensor})
        body.is_valid(raise_exception=True)
        services.save_alert_config(sensor, user=request.user, **body.validated_data)

        data = SensorDeviceSerializer(sensor).data
        # Báo các tab khác vẽ lại ô ngưỡng + đường ngưỡng trên biểu đồ. Redis hỏng thì ngưỡng
        # vẫn đã lưu — không biến việc lưu thành công thành lỗi 500.
        try:
            events.broadcast(events.sensor_alert_event(data))
        except Exception:
            logger.exception("Không phát được sự kiện sensor.alert")
        return Response(data)

    @extend_schema(responses={200: LatestReadingSerializer(many=True), **error_responses(401)})
    @action(detail=False, url_path="latest", **PLAIN_ARRAY)
    def latest(self, request):
        # Bảng rỗng → [] (UC-01 A1). Không dùng 204 từ bản 2.0 — 05-API.md §4.1.
        return Response(LatestReadingSerializer(services.latest_readings(), many=True).data)

    @extend_schema(
        parameters=[OpenApiParameter("limit", int, description="Số chu kỳ, 1 → 100, mặc định 20")],
        responses={200: ChartPointSerializer(many=True), **error_responses(400, 401)},
    )
    @action(detail=False, url_path="chart", **PLAIN_ARRAY)
    def chart(self, request):
        query = ChartQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)               # limit=abc → 400
        points = services.chart_cycles(query.validated_data["limit"])
        return Response(ChartPointSerializer(points, many=True).data)
