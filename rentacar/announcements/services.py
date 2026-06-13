from django.db.models import Q
from django.utils import timezone

from .models import Announcement, AnnouncementRead


def _audience_filter(user):
    if user.is_customer:
        return Q(audience__in=[Announcement.Audience.ALL, Announcement.Audience.CUSTOMERS])
    if user.is_owner:
        return Q(audience__in=[Announcement.Audience.ALL, Announcement.Audience.OWNERS])
    return Q(pk__in=[])


def active_announcements_queryset(user):
    if not user.is_authenticated or user.is_platform_admin:
        return Announcement.objects.none()
    now = timezone.now()
    return Announcement.objects.filter(
        _audience_filter(user),
        is_active=True,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now),
    )


def announcements_for_user(user):
    return active_announcements_queryset(user).order_by('-published_at')


def unread_announcements_for_user(user):
    read_ids = AnnouncementRead.objects.filter(user=user).values_list('announcement_id', flat=True)
    return announcements_for_user(user).exclude(pk__in=read_ids)


def unread_count_for_user(user):
    return unread_announcements_for_user(user).count()


def banner_announcement_for_user(user):
    read_map = {
        r.announcement_id: r
        for r in AnnouncementRead.objects.filter(user=user).select_related('announcement')
    }
    for ann in announcements_for_user(user):
        record = read_map.get(ann.id)
        if record and record.banner_dismissed_at:
            continue
        return ann
    return None


def mark_announcement_read(announcement, user):
    record, _ = AnnouncementRead.objects.get_or_create(
        announcement=announcement,
        user=user,
    )
    if not record.read_at:
        record.read_at = timezone.now()
        record.save(update_fields=['read_at'])
    return record


def dismiss_announcement_banner(announcement, user):
    record, _ = AnnouncementRead.objects.get_or_create(
        announcement=announcement,
        user=user,
    )
    now = timezone.now()
    record.banner_dismissed_at = now
    if not record.read_at:
        record.read_at = now
    record.save(update_fields=['banner_dismissed_at', 'read_at'])
    return record
