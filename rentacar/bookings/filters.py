import django_filters

from .models import Booking


class BookingFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status')
    rental_type = django_filters.CharFilter(field_name='rental_type')

    class Meta:
        model = Booking
        fields = ['status', 'rental_type']
