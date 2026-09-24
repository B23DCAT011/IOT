"""Vòng đời một lệnh điều khiển — 04-Database.md §5.3, §6; 03-Sequence.md SD-01, SD-02, SD-05.

    send_command()             PENDING   ← POST /api/devices/{id}/control   (tiến trình API)
    confirm_command()          SUCCESS   ← topic device_respond             (mqtt_worker)
    expire_pending_commands()  FAILED    ← vòng quét mỗi 1 giây             (mqtt_worker)

Ngoài vòng đời lệnh:
    sync_reported_state()      thiết bị tự báo trạng thái thật khi (kết nối lại) broker

`devices.current_state` chỉ được cập nhật ở HAI chỗ, cả hai đều do phần cứng xác nhận:
nhánh SUCCESS của confirm_command() và sync_reported_state().
"""
import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from config.exceptions import BrokerUnavailable, DeviceBusy

from .models import ActionHistory, Device
from .mqtt_publisher import MqttPublishError, publish_control

logger = logging.getLogger(__name__)

PENDING = ActionHistory.Status.PENDING
SUCCESS = ActionHistory.Status.SUCCESS
FAILED = ActionHistory.Status.FAILED

# Giá trị `status` của gói thiết bị tự báo trạng thái trên topic device_respond (không có request_id)
STATE_REPORT = "REPORT"

TIMEOUT_MESSAGE = (f"Timeout: không nhận được device_respond trong "
                   f"{settings.DEVICE_RESPONSE_TIMEOUT_SECONDS} giây")


def send_command(device, action, user):
    """Ghi bản ghi PENDING (BR-05) rồi publish lệnh lên broker.

    - Thiết bị còn lệnh PENDING → 409 DEVICE_BUSY, không ghi gì (BR-04, UC-02 E6).
    - Publish thất bại → xoá bản ghi vừa ghi → 503, không để lại lịch sử (UC-02 E2).
      Hệ quả: dãy id của bảng lịch sử có lỗ hổng — hành vi bình thường của PostgreSQL.

    ⚠️ Lệch có chủ đích so với mã mẫu 05-API.md §7.4 (publish BÊN TRONG transaction.atomic):
    bản ghi PENDING phải COMMIT xong TRƯỚC khi publish. Nếu không, thiết bị trả lời nhanh
    hơn lúc commit thì worker không thấy bản ghi, bỏ qua phản hồi, 5 giây sau đánh FAILED
    trong khi đèn đã bật thật. Đo được khi chạy thử: ESP giả lập trả lời sau ~20 ms.
    """
    with transaction.atomic():
        # Khoá dòng thiết bị: hai request đồng thời (2 tab, ca T-15) phải xếp hàng,
        # nếu không cả hai cùng thấy "không bận" và cùng ghi PENDING.
        Device.objects.select_for_update().get(pk=device.pk)
        if ActionHistory.objects.filter(device=device, status=PENDING).exists():
            raise DeviceBusy()
        record = ActionHistory.objects.create(device=device, action=action, user=user)

    try:
        publish_control(record.request_id, device.code, action)
    except MqttPublishError as exc:
        record.delete()
        logger.warning("Không gửi được lệnh %s %s lên broker: %s", device.code, action, exc)
        raise BrokerUnavailable() from exc

    logger.info("Đã gửi lệnh %s %s (request_id=%s, người thao tác=%s)",
                device.code, action, record.request_id, user)
    return record


def confirm_command(request_id, device_code, state, status):
    """Xử lý một message `device_respond`. Trả về bản ghi đã kết thúc, hoặc None nếu bỏ qua.

    Điều kiện `status=PENDING` nằm ngay trong truy vấn nên phản hồi đến muộn (lệnh đã hết
    giờ) và message QoS 1 bị broker gửi lại đều rơi vào nhánh bỏ qua — UC-02 E5.
    `select_for_update` chặn vòng quét timeout chạm vào cùng bản ghi đúng lúc 5 giây.
    """
    try:
        request_id = uuid.UUID(str(request_id))
    except ValueError:
        logger.warning("Bỏ qua device_respond: request_id '%s' không phải UUID", request_id)
        return None

    with transaction.atomic():
        record = (ActionHistory.objects
                  .select_for_update(of=("self",))
                  .select_related("device")
                  .filter(request_id=request_id, status=PENDING)
                  .first())
        if record is None:
            logger.info("Bỏ qua device_respond %s: không có lệnh PENDING tương ứng "
                        "(đã hết giờ, đã xử lý, hoặc lệnh không gửi qua API)", request_id)
            return None

        device = record.device
        if device_code != device.code:
            logger.warning("device_respond %s: mã thiết bị '%s' khác '%s' của lệnh gốc",
                           request_id, device_code, device.code)

        record.responded_at = timezone.now()
        if status == SUCCESS:
            if state != record.action:
                logger.warning("device_respond %s: firmware báo state=%s nhưng lệnh là %s",
                               request_id, state, record.action)
            record.status = SUCCESS
            record.save(update_fields=["status", "responded_at"])    # KHÔNG đụng user_id
            device.current_state = record.action
            device.save(update_fields=["current_state", "updated_at"])
        else:
            record.status = FAILED
            record.error_message = f"Thiết bị báo lỗi: status={status}"[:255]
            record.save(update_fields=["status", "responded_at", "error_message"])

    logger.info("Lệnh %s %s %s → %s (%s ms)", record.pk, device.code, record.action,
                record.status, record.latency_ms)
    return record


def sync_reported_state(device_code, state):
    """Thiết bị báo trạng thái THẬT khi (kết nối lại) broker. Trả về Device nếu vừa đổi, None nếu không.

    Tình huống: đèn đang ON thì rút điện mạch → cắm lại, firmware đặt mọi chân về LOW nên
    đèn tắt, nhưng CSDL vẫn ghi ON (04-Database.md §14 điểm 4). Giữ đúng nguyên tắc
    `current_state` = trạng thái vật lý ĐÃ XÁC NHẬN: phần cứng nói gì thì ghi nấy.
    Không ghi Action History — đây không phải lệnh do người bấm.
    """
    if state not in Device.State.values:
        logger.warning("Bỏ qua báo trạng thái của '%s': state=%r không hợp lệ", device_code, state)
        return None
    device = Device.objects.filter(code=device_code, is_active=True).first()
    if device is None:
        logger.warning("Bỏ qua báo trạng thái: không có thiết bị '%s'", device_code)
        return None
    if device.current_state == state:
        return None

    logger.info("Đồng bộ %s theo phần cứng: %s → %s", device.code, device.current_state, state)
    device.current_state = state
    device.save(update_fields=["current_state", "updated_at"])
    return device


def expire_pending_commands():
    """BR-03: lệnh PENDING quá 5 giây → FAILED. Trả về danh sách bản ghi vừa hết giờ.

    Vẫn phải đặt `responded_at` dù không có phản hồi nào — ràng buộc
    `action_responded_consistency` bắt buộc (04-Database.md §4.5). `current_state` giữ nguyên.
    `skip_locked`: bản ghi đang được confirm_command() khoá thì để lượt quét sau.
    """
    now = timezone.now()
    deadline = now - timedelta(seconds=settings.DEVICE_RESPONSE_TIMEOUT_SECONDS)

    with transaction.atomic():
        expired = list(ActionHistory.objects
                       .select_for_update(of=("self",), skip_locked=True)
                       .select_related("device")
                       .filter(status=PENDING, created_at__lt=deadline))
        if not expired:
            return []
        ActionHistory.objects.filter(pk__in=[r.pk for r in expired]).update(
            status=FAILED, responded_at=now, error_message=TIMEOUT_MESSAGE)

    for record in expired:
        record.status, record.responded_at, record.error_message = FAILED, now, TIMEOUT_MESSAGE
        logger.warning("Lệnh %s %s %s hết giờ sau %s ms", record.pk, record.device.code,
                       record.action, record.latency_ms)
    return expired
