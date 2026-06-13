from datetime import datetime, timezone as dt_timezone

from django.db.models import Q
from django.utils import timezone

from bookings.models import Booking
from rentacar.utils import format_display_name

from .models import BookingMessage, BookingThreadRead
from .permissions import can_view_thread


def accessible_bookings_queryset(user):
    qs = Booking.objects.select_related('customer', 'car', 'car__owner').prefetch_related('car__images')
    if user.is_platform_admin:
        return qs
    return qs.filter(Q(customer=user) | Q(car__owner=user))


def get_booking_for_user(user, booking_id):
    booking = accessible_bookings_queryset(user).filter(pk=booking_id).first()
    if booking and can_view_thread(user, booking):
        return booking
    return None


def create_text_message(booking, sender, body):
    body = (body or '').strip()
    if not body:
        raise ValueError('Message body is required.')
    return BookingMessage.objects.create(
        booking=booking,
        sender=sender,
        message_type=BookingMessage.MessageType.TEXT,
        body=body,
    )


def create_system_message(booking, body):
    body = (body or '').strip()
    if not body:
        raise ValueError('System message body is required.')
    return BookingMessage.objects.create(
        booking=booking,
        sender=None,
        message_type=BookingMessage.MessageType.SYSTEM,
        body=body,
    )


def create_location_message(booking, sender, latitude, longitude, label='', accuracy=None):
    body = (label or 'Current location').strip()
    metadata = {
        'latitude': latitude,
        'longitude': longitude,
        'label': body,
    }
    if accuracy is not None:
        metadata['accuracy'] = accuracy
    return BookingMessage.objects.create(
        booking=booking,
        sender=sender,
        message_type=BookingMessage.MessageType.LOCATION,
        body=body,
        metadata=metadata,
    )


def create_note_message(booking, customer, note):
    note = (note or '').strip()
    if not note:
        return None
    return BookingMessage.objects.create(
        booking=booking,
        sender=customer,
        message_type=BookingMessage.MessageType.TEXT,
        body=note,
    )


def mark_thread_read(booking, user):
    now = timezone.now()
    BookingThreadRead.objects.update_or_create(
        booking=booking,
        user=user,
        defaults={'last_read_at': now},
    )
    return now


def _read_at_for_user(booking_id, user_id):
    try:
        return BookingThreadRead.objects.get(booking_id=booking_id, user_id=user_id).last_read_at
    except BookingThreadRead.DoesNotExist:
        return None


def unread_count_for_booking(booking_id, user_id):
    read_at = _read_at_for_user(booking_id, user_id)
    qs = BookingMessage.objects.filter(booking_id=booking_id).exclude(sender_id=user_id)
    if read_at:
        qs = qs.filter(created_at__gt=read_at)
    return qs.count()


def total_unread_count(user):
    booking_ids = accessible_bookings_queryset(user).values_list('id', flat=True)
    total = 0
    for booking_id in booking_ids:
        total += unread_count_for_booking(booking_id, user.id)
    return total


def sender_display_name(user):
    if not user:
        return 'RentACar'
    return format_display_name(user.username) or user.username


def sender_role_label(user):
    if not user:
        return 'system'
    if user.is_platform_admin:
        return 'admin'
    return user.role


def other_party_for_user(user, booking):
    if user.is_platform_admin:
        return {
            'id': booking.customer_id,
            'name': sender_display_name(booking.customer),
            'role': 'customer',
            'subtitle': f'Owner: {sender_display_name(booking.car.owner)}',
        }
    if booking.customer_id == user.id:
        return {
            'id': booking.car.owner_id,
            'name': sender_display_name(booking.car.owner),
            'role': 'owner',
            'subtitle': None,
        }
    return {
        'id': booking.customer_id,
        'name': sender_display_name(booking.customer),
        'role': 'customer',
        'subtitle': None,
    }


def car_label(booking):
    car = booking.car
    return f'{car.brand} {car.model} ({car.year})'


def car_image_url(booking, request=None):
    car = booking.car
    images = list(car.images.all())
    image = next((img for img in images if img.is_primary), None)
    if not image and images:
        image = images[0]
    if image and image.image:
        url = image.image.url
        if request:
            return request.build_absolute_uri(url)
        return url
    return None


def thread_context_for_booking(booking, user, request=None):
    other = other_party_for_user(user, booking)
    return {
        'booking_id': booking.id,
        'car_id': booking.car_id,
        'car_label': car_label(booking),
        'car_image_url': car_image_url(booking, request),
        'car_location': booking.car.location,
        'rental_period': booking.get_duration_label(),
        'total_cost': str(booking.total_cost),
        'booking_status': booking.status,
        'other_party_id': other['id'],
        'other_party_name': other['name'],
        'other_party_role': other['role'],
        'other_party_subtitle': other.get('subtitle'),
        'is_open': booking.status in {'pending', 'approved'},
    }


def last_message_preview(message):
    if not message:
        return ''
    if message.message_type == BookingMessage.MessageType.SYSTEM:
        return message.body
    if message.message_type == BookingMessage.MessageType.LOCATION:
        label = (message.metadata or {}).get('label') or message.body or 'Location'
        prefix = ''
        if message.sender_id:
            prefix = f'{sender_display_name(message.sender)}: '
        return f'{prefix}📍 {label}'
    prefix = ''
    if message.sender_id:
        prefix = f'{sender_display_name(message.sender)}: '
    return f'{prefix}{message.body}'


def thread_summaries_for_user(user):
    bookings = list(
        accessible_bookings_queryset(user).order_by('-updated_at', '-created_at')
    )
    if not bookings:
        return []

    booking_ids = [b.id for b in bookings]
    last_messages = {}
    for msg in BookingMessage.objects.filter(booking_id__in=booking_ids).select_related('sender').order_by('booking_id', '-created_at'):
        if msg.booking_id not in last_messages:
            last_messages[msg.booking_id] = msg

    summaries = []
    for booking in bookings:
        unread = unread_count_for_booking(booking.id, user.id)
        other = other_party_for_user(user, booking)
        last_msg = last_messages.get(booking.id)
        summaries.append({
            'booking_id': booking.id,
            'booking_status': booking.status,
            'car_id': booking.car_id,
            'car_label': car_label(booking),
            'car_location': booking.car.location,
            'other_party_id': other['id'],
            'other_party_name': other['name'],
            'other_party_role': other['role'],
            'other_party_subtitle': other.get('subtitle'),
            'rental_period': booking.get_duration_label(),
            'last_message': last_message_preview(last_msg),
            'last_message_at': last_msg.created_at if last_msg else None,
            'unread_count': unread,
            'is_open': booking.status in {'pending', 'approved'},
        })

    min_dt = datetime.min.replace(tzinfo=dt_timezone.utc)
    summaries.sort(key=lambda s: s['last_message_at'] or min_dt, reverse=True)
    return summaries


def counterparty_read_at(booking, user):
    """When the other participant last read the thread (for read receipts)."""
    if user.is_platform_admin:
        targets = [booking.customer_id, booking.car.owner_id]
    elif booking.customer_id == user.id:
        targets = [booking.car.owner_id]
    else:
        targets = [booking.customer_id]

    latest = None
    for uid in targets:
        read_at = _read_at_for_user(booking.id, uid)
        if read_at and (latest is None or read_at > latest):
            latest = read_at
    return latest
