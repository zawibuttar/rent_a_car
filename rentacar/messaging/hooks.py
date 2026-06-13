"""System messages for booking lifecycle events."""
from .services import create_system_message


def on_booking_created(booking):
    create_system_message(
        booking,
        'Booking request submitted. You can use this thread to coordinate pickup and details.',
    )


def on_booking_note(booking, customer, note):
    from .services import create_note_message
    create_note_message(booking, customer, note)


def on_booking_status_changed(booking, new_status, actor_label=None):
    labels = {
        'approved': 'Booking approved by the owner.',
        'rejected': 'Booking rejected by the owner.',
        'cancelled': 'Booking cancelled by the customer.',
        'completed': 'Booking marked as completed.',
    }
    body = labels.get(new_status)
    if not body:
        return None
    if actor_label and new_status in ('approved', 'rejected', 'cancelled', 'completed'):
        if new_status == 'cancelled':
            body = f'Booking cancelled by {actor_label}.'
        elif new_status == 'completed':
            body = f'Booking marked as completed by {actor_label}.'
        elif new_status == 'approved':
            body = f'Booking approved by {actor_label}.'
        elif new_status == 'rejected':
            body = f'Booking rejected by {actor_label}.'
    return create_system_message(booking, body)
