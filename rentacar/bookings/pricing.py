"""Rental duration validation and cost calculation."""
from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from django.utils import timezone

RENTAL_HOURLY = 'hourly'
RENTAL_DAILY = 'daily'
RENTAL_WEEKLY = 'weekly'
RENTAL_MONTHLY = 'monthly'

RENTAL_TYPE_CHOICES = (
    (RENTAL_HOURLY, 'Hourly'),
    (RENTAL_DAILY, 'Daily'),
    (RENTAL_WEEKLY, 'Weekly'),
    (RENTAL_MONTHLY, 'Monthly'),
)

CAR_RENTAL_FIELDS = {
    RENTAL_HOURLY: ('rent_hourly', 'price_per_hour'),
    RENTAL_DAILY: ('rent_daily', 'price_per_day'),
    RENTAL_WEEKLY: ('rent_weekly', 'price_per_week'),
    RENTAL_MONTHLY: ('rent_monthly', 'price_per_month'),
}


def _money(value):
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _hourly_elapsed_hours(start_at, end_at):
    return Decimal(str((end_at - start_at).total_seconds() / 3600))


def _hourly_duration_label(start_at, end_at):
    total_seconds = int((end_at - start_at).total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours and minutes:
        return f'{hours}h {minutes}m'
    if hours:
        return f'{hours}h'
    return f'{minutes}m'


def _inclusive_calendar_days(start_at, end_at):
    return (end_at.date() - start_at.date()).days + 1


def day_start(dt):
    """Start of calendar day in the active timezone."""
    local = timezone.localtime(dt) if timezone.is_aware(dt) else dt
    d = local.date()
    return timezone.make_aware(datetime.combine(d, time.min))


def day_end(dt):
    """End of calendar day in the active timezone."""
    local = timezone.localtime(dt) if timezone.is_aware(dt) else dt
    d = local.date()
    return timezone.make_aware(datetime.combine(d, time(23, 59, 59)))


def normalize_booking_window(rental_type, start_at, end_at):
    """
    Normalize UI/API datetimes to stored booking intervals.
    Daily+ types expand to full calendar days.
    """
    if rental_type == RENTAL_HOURLY:
        return start_at, end_at
    if rental_type == RENTAL_DAILY:
        return day_start(start_at), day_end(end_at)
    if rental_type in (RENTAL_WEEKLY, RENTAL_MONTHLY):
        return day_start(start_at), day_end(end_at)
    return start_at, end_at


def validate_rental_window(car, rental_type, start_at, end_at):
    """Return None if valid, else error message string."""
    if rental_type not in dict(RENTAL_TYPE_CHOICES):
        return 'Invalid rental type.'

    flag_field, price_field = CAR_RENTAL_FIELDS[rental_type]
    if not getattr(car, flag_field, False):
        return f'This car is not available for {rental_type} rental.'
    price = getattr(car, price_field, None)
    if price is None or price <= 0:
        return f'Price for {rental_type} rental is not configured.'

    now = timezone.now()
    if timezone.is_naive(start_at):
        start_at = timezone.make_aware(start_at)
    if timezone.is_naive(end_at):
        end_at = timezone.make_aware(end_at)

    if rental_type == RENTAL_HOURLY:
        if start_at < now - timedelta(minutes=1):
            return 'Pick-up cannot be in the past.'
        if end_at <= start_at:
            return 'Return must be after pick-up.'
        hours = (end_at - start_at).total_seconds() / 3600
        if hours < 1:
            return 'Minimum rental is 1 hour.'
        return None

    start_day = timezone.localtime(start_at).date()
    if start_day < timezone.localdate():
        return 'Pick-up cannot be in the past.'

    if end_at < start_at:
        return 'Return cannot be before pick-up.'

    days = _inclusive_calendar_days(start_at, end_at)
    if rental_type == RENTAL_DAILY:
        if days < 1:
            return 'Invalid date range.'
        return None
    if rental_type == RENTAL_WEEKLY:
        if days < 7:
            return 'Minimum weekly rental is 7 days.'
        return None
    if rental_type == RENTAL_MONTHLY:
        if days < 30:
            return 'Minimum monthly rental is 30 days.'
        return None
    return None


def compute_total(car, rental_type, start_at, end_at):
    """Compute total cost; raises ValueError with message if invalid."""
    err = validate_rental_window(car, rental_type, start_at, end_at)
    if err:
        raise ValueError(err)

    start_at, end_at = normalize_booking_window(rental_type, start_at, end_at)

    if rental_type == RENTAL_HOURLY:
        hours = _hourly_elapsed_hours(start_at, end_at)
        return _money(hours * car.price_per_hour)

    days = _inclusive_calendar_days(start_at, end_at)
    days = max(days, 1)

    if rental_type == RENTAL_DAILY:
        price = car.get_final_price() if hasattr(car, 'get_final_price') else car.price_per_day
        return _money(days * price)
    if rental_type == RENTAL_WEEKLY:
        weeks = ceil(days / 7)
        return _money(weeks * car.price_per_week)
    if rental_type == RENTAL_MONTHLY:
        months = ceil(days / 30)
        return _money(months * car.price_per_month)

    raise ValueError('Invalid rental type.')


def duration_label(rental_type, start_at, end_at):
    """Human-readable duration for dashboards."""
    if not start_at or not end_at:
        return '—'
    start_at, end_at = normalize_booking_window(rental_type, start_at, end_at)

    if rental_type == RENTAL_HOURLY:
        return _hourly_duration_label(start_at, end_at)

    days = _inclusive_calendar_days(start_at, end_at)
    if rental_type == RENTAL_DAILY:
        return f'{days}d'
    if rental_type == RENTAL_WEEKLY:
        weeks = ceil(days / 7)
        return f'{weeks}w'
    if rental_type == RENTAL_MONTHLY:
        months = ceil(days / 30)
        return f'{months}mo'
    return '—'


def format_period(rental_type, start_at, end_at):
    """Display pick-up → return for tables."""
    if not start_at or not end_at:
        return '—'
    if rental_type == RENTAL_HOURLY:
        fmt = '%b %d, %Y %H:%M'
        s = timezone.localtime(start_at).strftime(fmt) if timezone.is_aware(start_at) else start_at.strftime(fmt)
        e = timezone.localtime(end_at).strftime(fmt) if timezone.is_aware(end_at) else end_at.strftime(fmt)
        return f'{s} → {e}'
    fmt = '%Y-%m-%d'
    s = timezone.localtime(start_at).date().isoformat() if timezone.is_aware(start_at) else start_at.date().isoformat()
    e = timezone.localtime(end_at).date().isoformat() if timezone.is_aware(end_at) else end_at.date().isoformat()
    return f'{s} → {e}'
