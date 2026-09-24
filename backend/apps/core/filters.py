"""Hai mảnh dùng chung cho bộ lọc của /api/sensors và /api/actions (UC-04)."""
from django import forms
from rest_framework.filters import OrderingFilter

from config.exceptions import INVALID_RANGE_CODE


class RangeCheckForm(forms.Form):
    """Form nền của FilterSet: chặn khoảng lọc ngược (`…__gte` > `…__lte`) — UC-04 E2.

    Lớp con chỉ cần khai `range_pairs`. Lỗi được gắn mã `invalid_range` để bộ xử lý
    ngoại lệ trả `400 INVALID_RANGE` thay vì `VALIDATION_ERROR` (05-API.md §2.7).
    """

    range_pairs = []   # [("recorded_at__gte", "recorded_at__lte"), …]

    def clean(self):
        cleaned = super().clean()
        for low, high in self.range_pairs:
            a, b = cleaned.get(low), cleaned.get(high)
            if a is not None and b is not None and a > b:
                self.add_error(low, forms.ValidationError(
                    "Giá trị đầu khoảng phải nhỏ hơn hoặc bằng giá trị cuối khoảng.",
                    code=INVALID_RANGE_CODE,
                ))
        return cleaned


class TiebreakOrderingFilter(OrderingFilter):
    """OrderingFilter luôn nối thêm cột phá hoà — 05-API.md §7.3 điểm 3.

    `?ordering=-value` bình thường THAY THẾ toàn bộ thứ tự mặc định, nên các dòng bằng
    nhau (cùng giá trị, hoặc 3 số đo cùng một chu kỳ) đổi chỗ tuỳ ý giữa hai lần gọi →
    lật trang bị lặp/mất dòng. View khai `ordering_tiebreak` để chốt thứ tự duy nhất.
    """

    def get_ordering(self, request, queryset, view):
        ordering = list(super().get_ordering(request, queryset, view) or [])
        used = {field.lstrip("-") for field in ordering}
        for field in getattr(view, "ordering_tiebreak", []):
            if field.lstrip("-") not in used:
                ordering.append(field)
                used.add(field.lstrip("-"))
        return ordering
