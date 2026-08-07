from rest_framework import serializers

from rentacar.image_validation import validate_car_image_file

from .models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    banner_dismissed = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'body', 'image_url', 'audience', 'is_active',
            'published_at', 'expires_at', 'is_expired',
            'created_by_name', 'is_read', 'banner_dismissed',
        ]
        read_only_fields = [
            'id', 'published_at', 'is_expired', 'created_by_name', 'is_read', 'banner_dismissed', 'image_url',
        ]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url

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
    image = serializers.FileField(required=False, allow_null=True)
    remove_image = serializers.BooleanField(required=False, write_only=True, default=False)

    class Meta:
        model = Announcement
        fields = ['title', 'body', 'audience', 'is_active', 'expires_at', 'image', 'remove_image']

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

    def validate_is_active(self, value):
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    def validate_remove_image(self, value):
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    def validate_image(self, value):
        if not value:
            return value
        err = validate_car_image_file(value)
        if err:
            raise serializers.ValidationError(err)
        return value

    def create(self, validated_data):
        validated_data.pop('remove_image', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        remove_image = validated_data.pop('remove_image', False)
        image = validated_data.pop('image', serializers.empty)
        instance = super().update(instance, validated_data)
        if remove_image and instance.image:
            instance.image.delete(save=False)
            instance.image = None
            instance.save(update_fields=['image'])
        elif image is not serializers.empty and image is not None:
            if instance.image:
                instance.image.delete(save=False)
            instance.image = image
            instance.save(update_fields=['image'])
        return instance
