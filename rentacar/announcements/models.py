from django.conf import settings
from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    class Audience(models.TextChoices):
        ALL = 'all', 'All users'
        CUSTOMERS = 'customers', 'Customers'
        OWNERS = 'owners', 'Owners'

    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=Audience.choices, default=Audience.ALL)
    is_active = models.BooleanField(default=True, db_index=True)
    published_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='announcements_created',
    )

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return self.expires_at is not None and self.expires_at <= timezone.now()


class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='reads',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcement_reads',
    )
    read_at = models.DateTimeField(auto_now_add=True)
    banner_dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('announcement', 'user')]
        indexes = [
            models.Index(fields=['user', 'announcement']),
        ]

    def __str__(self):
        return f'user={self.user_id} announcement={self.announcement_id}'
