"""Các endpoint /api/sensors (05-API.md §4.0 → §4.3)."""
import logging

from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

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

# Endpoint phụ: trả mảng thuần, không phân trang, không lọc.
PLAIN_ARRAY = {"pagination_class": None, "filter_backends": []}


class SensorViewSet(ReadOnlyModelViewSet):
    # list()     → GET /api/sensors        bảng Data Sensor: lọc, tìm, sắp xếp, phân trang
    # retrieve() → GET /api/sensors/{id}   một số đo

    queryset = SensorData.objects.select_related("sensor")   # JOIN sẵn cảm biến, tránh N+1 truy vấn
    serializer_class = SensorReadingSerializer
    filterset_class = SensorDataFilter                        # ?sensor= &value__gte= &recorded_at__gte= ...
    search_fields = ["sensor__code", "sensor__name"]          # ?search=
    ordering_fields = ["recorded_at", "value", "id"]          # ?ordering=
    ordering = ["-recorded_at", "sensor_id"]                  # mặc định: mới nhất trước
    ordering_tiebreak = ["sensor_id", "id"]                   # phá hoà để phân trang không lặp dòng

    # GET /api/sensors/devices — danh mục cảm biến kèm ngưỡng (Dashboard)
    @action(detail=False, url_path="devices", **PLAIN_ARRAY)
    def devices(self, request):
        sensors = SensorDevice.objects.filter(is_active=True).select_related("alert_updated_by")
        return Response(SensorDeviceSerializer(sensors, many=True).data)

    # PUT /api/sensors/devices/{id}/alert — sửa ngưỡng cảnh báo (nút ⚙ trên Dashboard)
    @action(detail=False, methods=["put"], url_path=r"devices/(?P<sensor_id>\d+)/alert",
            **PLAIN_ARRAY)
    def alert(self, request, sensor_id=None):
        sensor = get_object_or_404(SensorDevice.objects.filter(is_active=True), pk=sensor_id)
        body = AlertConfigSerializer(data=request.data, context={"sensor": sensor})
        body.is_valid(raise_exception=True)                   # sai → 400
        services.save_alert_config(sensor, user=request.user, **body.validated_data)

        data = SensorDeviceSerializer(sensor).data
        # Báo các tab khác cập nhật ngưỡng. Redis lỗi thì bỏ qua: ngưỡng đã lưu xong.
        try:
            events.broadcast(events.sensor_alert_event(data))
        except Exception:
            logger.exception("Không phát được sự kiện sensor.alert")
        return Response(data)

    # GET /api/sensors/latest — số đo mới nhất của từng cảm biến (3 thẻ trên Dashboard)
    @action(detail=False, url_path="latest", **PLAIN_ARRAY)
    def latest(self, request):
        return Response(LatestReadingSerializer(services.latest_readings(), many=True).data)   # rỗng → []

    # GET /api/sensors/chart?limit=20 — N chu kỳ gần nhất cho biểu đồ Dashboard
    @action(detail=False, url_path="chart", **PLAIN_ARRAY)
    def chart(self, request):
        query = ChartQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)                  # limit=abc → 400
        points = services.chart_cycles(query.validated_data["limit"])
        return Response(ChartPointSerializer(points, many=True).data)
