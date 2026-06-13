from django.conf import settings
from django.db import models

from bookings.models import Booking


class BookingMessage(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'text', 'Text'
        SYSTEM = 'system', 'System'
        LOCATION = 'location', 'Location'
        ATTACHMENT = 'attachment', 'Attachment'

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking_messages_sent',
    )
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    body = models.TextField()
    metadata = models.JSONField(blank=True, null=True)
    attachment = models.FileField(upload_to='message_attachments/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['booking', 'created_at']),
        ]

    def __str__(self):
        return f'Message #{self.pk} on booking #{self.booking_id}'


class BookingThreadRead(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='thread_reads',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='booking_thread_reads',
    )
    last_read_at = models.DateTimeField()

    class Meta:
        unique_together = [('booking', 'user')]
        indexes = [
            models.Index(fields=['user', 'booking']),
        ]

    def __str__(self):
        return f'Read cursor user={self.user_id} booking={self.booking_id}'
