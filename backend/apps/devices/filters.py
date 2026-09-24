"""Tham số lọc của GET /api/actions — 05-API.md §4.6; UC-04."""
from django import forms
from django_filters import rest_framework as filters

from apps.core.filters import RangeCheckForm

from .models import ActionHistory

NO_USER = "none"


class ActionHistoryFilterForm(RangeCheckForm):
    range_pairs = [("created_at__gte", "created_at__lte")]

    def clean_user(self):
        value = self.cleaned_data.get("user")
        if value and value != NO_USER and not (value.isascii() and value.isdigit()):
            raise forms.ValidationError('Phải là số nguyên hoặc "none".')
        return value


class ActionHistoryFilter(filters.FilterSet):
    device = filters.NumberFilter(field_name="device_id")
    # `?user=2` lọc theo người thao tác; `?user=none` lọc các lệnh KHÔNG rõ ai phát ra.
    # Cần giá trị đặc biệt vì `?user=` bỏ trống bị hiểu là "không lọc" (BR-12).
    user = filters.CharFilter(method="filter_user")
    status = filters.ChoiceFilter(choices=ActionHistory.Status.choices)
    action = filters.ChoiceFilter(choices=ActionHistory.Action.choices)

    class Meta:
        model = ActionHistory
        form = ActionHistoryFilterForm
        fields = {"created_at": ["gte", "lte"]}

    def filter_user(self, queryset, name, value):
        if value == NO_USER:
            return queryset.filter(user__isnull=True)
        return queryset.filter(user_id=int(value))    # đã kiểm là số ở clean_user
