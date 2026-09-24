"""Bộ xử lý lỗi thống nhất — 05-API.md §2.6, §2.7, §7.5.

Mọi phản hồi lỗi của API có đúng MỘT hình dạng:

    {"error": {"code": "DEVICE_BUSY", "message": "…", "details": null}}

Frontend rẽ nhánh theo `code`, không so khớp theo `message`. Chỉ dùng 9 mã đã công bố
ở §2.7 — thêm mã mới thì phải thêm vào tài liệu trước.
"""
import logging

from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

# Mã gắn vào lỗi của form lọc khi đầu khoảng > cuối khoảng (apps/core/filters.py).
INVALID_RANGE_CODE = "invalid_range"


# ---------------------------------------------------------------------------
# Các ngoại lệ nghiệp vụ — view/service chỉ việc `raise`, bộ xử lý bên dưới lo phần JSON
# ---------------------------------------------------------------------------

class InvalidCredentials(APIException):
    status_code = status.HTTP_400_BAD_REQUEST      # cố ý KHÔNG dùng 401 — §2.7
    error_code = "INVALID_CREDENTIALS"
    default_detail = "Tên đăng nhập hoặc mật khẩu không đúng."


class DeviceBusy(APIException):
    status_code = status.HTTP_409_CONFLICT          # BR-04, UC-02 E6
    error_code = "DEVICE_BUSY"
    default_detail = ("Thiết bị đang chờ phản hồi cho lệnh trước đó, "
                      "vui lòng thử lại sau vài giây.")


class BrokerUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE   # UC-02 E2
    error_code = "BROKER_UNAVAILABLE"
    default_detail = "Không kết nối được tới hệ thống điều khiển (MQTT broker)."


class PageNotFound(NotFound):
    error_code = "PAGE_NOT_FOUND"                   # UC-03 A2
    default_detail = "Trang không tồn tại."


# ---------------------------------------------------------------------------
# Bảng tra mã lỗi và câu thông báo
# ---------------------------------------------------------------------------

CODE_BY_STATUS = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHENTICATED",
    404: "NOT_FOUND",
    409: "DEVICE_BUSY",
    500: "INTERNAL_ERROR",
    503: "BROKER_UNAVAILABLE",
}

# Câu chung cho lỗi theo từng trường — chi tiết từng ô nằm ở `details`.
FIELD_ERROR_MESSAGE = {
    "VALIDATION_ERROR": "Dữ liệu gửi lên không hợp lệ.",
    "INVALID_RANGE": "Khoảng lọc không hợp lệ.",
}

# Thay câu gốc của DRF ở những chỗ nó không dùng được: có nhiều biến thể cho cùng một
# nghĩa (thiếu/sai/thu hồi token) hoặc lộ chi tiết nội bộ ("No Device matches the given query.").
DETAIL_OVERRIDE = {
    "UNAUTHENTICATED": "Bạn chưa đăng nhập hoặc phiên đăng nhập đã hết.",
    "NOT_FOUND": "Không tìm thấy tài nguyên.",
}

INTERNAL_ERROR_MESSAGE = "Máy chủ gặp lỗi không mong muốn."


def _error_code(exc, status_code):
    code = getattr(exc, "error_code", None)
    if code:
        return code
    # Chỉ khi MỌI lỗi đều là khoảng ngược; lẫn lỗi khác thì trả VALIDATION_ERROR chung.
    if isinstance(exc, ValidationError) and _flatten_codes(exc.get_codes()) == {INVALID_RANGE_CODE}:
        return "INVALID_RANGE"
    if status_code in CODE_BY_STATUS:
        return CODE_BY_STATUS[status_code]
    # 405, 415… chỉ xảy ra khi bên gọi viết sai request — xếp chung nhóm lỗi đầu vào,
    # để không phát sinh mã thứ 10 ngoài danh sách đã công bố.
    return "VALIDATION_ERROR" if status_code < 500 else "INTERNAL_ERROR"


def _flatten_codes(codes):
    """`ValidationError.get_codes()` trả dict/list lồng nhau — gom mọi mã lỗi thành một set."""
    if isinstance(codes, dict):
        return set().union(*(_flatten_codes(v) for v in codes.values()))
    if isinstance(codes, list):
        return set().union(*(_flatten_codes(v) for v in codes))
    return {codes}


def _error_body(code, message, details=None):
    return {"error": {"code": code, "message": message, "details": details}}


# ---------------------------------------------------------------------------
# Hàm được khai ở REST_FRAMEWORK["EXCEPTION_HANDLER"]
# ---------------------------------------------------------------------------

def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        # Lỗi không do DRF sinh ra (bug, mất kết nối CSDL…) → vẫn trả đúng hình dạng JSON.
        logger.exception("Lỗi không lường trước ở %s", context.get("view"))
        return Response(
            _error_body("INTERNAL_ERROR", INTERNAL_ERROR_MESSAGE),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = _error_code(exc, response.status_code)
    data = response.data

    if isinstance(data, dict) and set(data) == {"detail"}:
        # Ngoại lệ đơn (NotFound, DeviceBusy, JSON hỏng…): chỉ có một câu thông báo.
        body = _error_body(code, DETAIL_OVERRIDE.get(code, str(data["detail"])))
    else:
        # Lỗi theo từng trường (serializer, bộ lọc): giữ nguyên chi tiết để Frontend tô đỏ đúng ô.
        details = data if isinstance(data, dict) else {"non_field_errors": data}
        message = FIELD_ERROR_MESSAGE.get(code, FIELD_ERROR_MESSAGE["VALIDATION_ERROR"])
        body = _error_body(code, message, details)

    response.data = body
    return response
