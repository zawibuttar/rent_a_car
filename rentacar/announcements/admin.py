from django.contrib import admin

from .models import Announcement, AnnouncementRead


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'is_active', 'published_at', 'expires_at', 'created_by')
    list_filter = ('audience', 'is_active')
    search_fields = ('title', 'body')


@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'user', 'read_at', 'banner_dismissed_at')
