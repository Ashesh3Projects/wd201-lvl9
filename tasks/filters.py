from django_filters.rest_framework import (
    CharFilter,
    ChoiceFilter,
    FilterSet,
    DateTimeFilter,
)

from tasks.models import STATUS_CHOICES


class TaskFilter(FilterSet):
    title = CharFilter(lookup_expr="icontains")
    status = ChoiceFilter(choices=STATUS_CHOICES)
    completed = ChoiceFilter(choices=((True, "True"), (False, "False")))


class TaskStatusChangeFilter(FilterSet):
    changed_date = DateTimeFilter(field_name="changed_date", lookup_expr="gte")
    original_status = ChoiceFilter(choices=STATUS_CHOICES)
    updated_status = ChoiceFilter(choices=STATUS_CHOICES)
