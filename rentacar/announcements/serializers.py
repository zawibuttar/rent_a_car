from rest_framework import serializers

from .models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    banner_dismissed = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'body', 'audience', 'is_active',
            'published_at', 'expires_at', 'is_expired',
            'created_by_name', 'is_read', 'banner_dismissed',
        ]
        read_only_fields = [
            'id', 'published_at', 'is_expired', 'created_by_name', 'is_read', 'banner_dismissed',
        ]

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return ''
        return obj.created_by.username

    def _read_record(self, obj):
        cache = self.context.get('read_map') or {}
        return cache.get(obj.id)

    def get_is_read(self, obj):
        return self._read_record(obj) is not None

    def get_banner_dismissed(self, obj):
        record = self._read_record(obj)
        return bool(record and record.banner_dismissed_at)


class AnnouncementWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['title', 'body', 'audience', 'is_active', 'expires_at']

    def validate_title(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Title is required.')
        return value

    def validate_body(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Body is required.')
        return value
