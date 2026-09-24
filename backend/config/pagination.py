"""Phân trang dùng chung cho /api/sensors và /api/actions — 05-API.md §2.8, BR-08."""
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination

from config.exceptions import PageNotFound


class StandardPagination(PageNumberPagination):
    page_size = 10                      # BR-08
    page_size_query_param = "page_size"
    max_page_size = 100                 # UC-04 E3 — lớn hơn thì tự hạ về 100, không báo lỗi

    def paginate_queryset(self, queryset, request, view=None):
        # Mặc định DRF im lặng bỏ qua `page_size=abc` và trả 200 (CLAUDE.md §0.2g, ca A-05).
        # Tài liệu yêu cầu sai KIỂU thì báo 400, còn sai KHOẢNG (500) thì tự hạ biên.
        self._require_positive_int(request, self.page_query_param)
        self._require_positive_int(request, self.page_size_query_param)
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound as exc:
            raise PageNotFound() from exc    # vượt tổng số trang → 404 PAGE_NOT_FOUND

    @staticmethod
    def _require_positive_int(request, name):
        raw = request.query_params.get(name)
        if raw is not None and not (raw.isascii() and raw.isdigit() and int(raw) >= 1):
            raise ValidationError({name: ["Phải là số nguyên dương."]})
