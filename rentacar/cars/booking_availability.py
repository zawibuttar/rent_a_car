"""Active booking windows for car list/detail APIs."""
from django.db.models import Prefetch
from django.utils import timezone

from bookings.models import Booking
from bookings.pricing import format_period

ACTIVE_BOOKING_STATUSES = ('pending', 'approved')


def active_bookings_queryset():
    now = timezone.now()
    return Booking.objects.filter(
        status__in=ACTIVE_BOOKING_STATUSES,
        end_at__gte=now,
    ).order_by('start_at')


def prefetch_active_bookings(queryset):
    return queryset.prefetch_related(
        Prefetch(
            'bookings',
            queryset=active_bookings_queryset(),
            to_attr='active_bookings',
        )
    )


def _booking_is_active_now(booking, now=None):
    now = now or timezone.now()
    return booking.start_at <= now < booking.end_at


def get_active_bookings_for_car(car):
    if hasattr(car, 'active_bookings'):
        return car.active_bookings
    return list(active_bookings_queryset().filter(car_id=car.pk))


def car_booking_availability(car, *, limit=None, include_status=True):
    """Return (slots, total_count, is_currently_booked) in one pass."""
    bookings = get_active_bookings_for_car(car)
    total = len(bookings)
    now = timezone.now()
    is_currently_booked = any(
        booking.start_at <= now < booking.end_at for booking in bookings
    )
    display_bookings = bookings[:limit] if limit is not None else bookings
    slots = []
    for booking in display_bookings:
        slot = {
            'rental_type': booking.rental_type,
            'start_at': booking.start_at.isoformat(),
            'end_at': booking.end_at.isoformat(),
            'period_display': format_period(
                booking.rental_type, booking.start_at, booking.end_at
            ),
            'is_active': _booking_is_active_now(booking, now),
        }
        if include_status:
            slot['status'] = booking.status
        slots.append(slot)
    return slots, total, is_currently_booked


def build_booked_slots(car, *, limit=None, include_status=True):
    slots, total, _ = car_booking_availability(
        car, limit=limit, include_status=include_status
    )
    return slots, total


def is_car_currently_booked(car):
    _, _, is_currently_booked = car_booking_availability(car)
    return is_currently_booked
