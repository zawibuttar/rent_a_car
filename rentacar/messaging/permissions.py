OPEN_BOOKING_STATUSES = frozenset({'pending', 'approved'})
CLOSED_BOOKING_STATUSES = frozenset({'rejected', 'cancelled', 'completed'})


def is_booking_participant(user, booking):
    if not user or not user.is_authenticated:
        return False
    return booking.customer_id == user.id or booking.car.owner_id == user.id


def can_view_thread(user, booking):
    if not user or not user.is_authenticated:
        return False
    return is_booking_participant(user, booking) or user.is_platform_admin


def can_post_message(user, booking):
    if not user or not user.is_authenticated:
        return False
    if user.is_platform_admin:
        return True
    if not is_booking_participant(user, booking):
        return False
    return booking.status in OPEN_BOOKING_STATUSES


def is_thread_open(booking):
    return booking.status in OPEN_BOOKING_STATUSES
