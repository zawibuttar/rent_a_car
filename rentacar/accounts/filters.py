import django_filters

from .models import OwnerProfile


class AdminOwnerFilter(django_filters.FilterSet):
    is_verified = django_filters.BooleanFilter(field_name='is_verified')

    class Meta:
        model = OwnerProfile
        fields = ['is_verified']
