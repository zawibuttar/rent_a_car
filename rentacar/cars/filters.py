import django_filters

from .models import Car


LISTING_CHOICES = (
    ('live', 'Live on marketplace'),
    ('hidden', 'Removed by admin'),
    ('admin_removed', 'Removed by admin'),
    ('paused', 'Paused by owner'),
    ('unavailable', 'Paused by owner'),
)


def _filter_listing(queryset, value):
    if value == 'live':
        return queryset.filter(is_approved=True, is_available=True)
    if value in ('hidden', 'admin_removed'):
        return queryset.filter(is_approved=False)
    if value in ('paused', 'unavailable'):
        return queryset.filter(is_available=False)
    return queryset


class AdminCarFilter(django_filters.FilterSet):
    car_type = django_filters.CharFilter(field_name='car_type')
    category = django_filters.CharFilter(field_name='category')
    is_approved = django_filters.BooleanFilter(field_name='is_approved')
    is_available = django_filters.BooleanFilter(field_name='is_available')
    listing = django_filters.ChoiceFilter(choices=LISTING_CHOICES, method='filter_listing')

    class Meta:
        model = Car
        fields = ['car_type', 'category', 'is_approved', 'is_available', 'listing']

    def filter_listing(self, queryset, name, value):
        return _filter_listing(queryset, value)


class OwnerCarFilter(django_filters.FilterSet):
    car_type = django_filters.CharFilter(field_name='car_type')
    category = django_filters.CharFilter(field_name='category')
    listing = django_filters.ChoiceFilter(choices=LISTING_CHOICES, method='filter_listing')

    class Meta:
        model = Car
        fields = ['car_type', 'category', 'listing']

    def filter_listing(self, queryset, name, value):
        if value == 'live':
            return queryset.filter(is_approved=True, is_available=True)
        if value in ('hidden', 'admin_removed'):
            return queryset.filter(is_approved=False)
        if value in ('paused', 'unavailable'):
            return queryset.filter(is_available=False)
        return queryset
