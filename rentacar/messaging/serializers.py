from rest_framework import serializers

from .models import BookingMessage
from .map_preview import map_preview_absolute_url
from .services import sender_display_name, sender_role_label


class ThreadSummarySerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    booking_status = serializers.CharField()
    car_id = serializers.IntegerField()
    car_label = serializers.CharField()
    car_location = serializers.CharField()
    other_party_id = serializers.IntegerField()
    other_party_name = serializers.CharField()
    other_party_role = serializers.CharField()
    other_party_subtitle = serializers.CharField(allow_null=True)
    rental_period = serializers.CharField()
    last_message = serializers.CharField()
    last_message_at = serializers.DateTimeField(allow_null=True)
    unread_count = serializers.IntegerField()
    is_open = serializers.BooleanField()


class ThreadContextSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    car_id = serializers.IntegerField()
    car_label = serializers.CharField()
    car_image_url = serializers.CharField(allow_null=True)
    car_location = serializers.CharField()
    rental_period = serializers.CharField()
    total_cost = serializers.CharField()
    booking_status = serializers.CharField()
    other_party_id = serializers.IntegerField()
    other_party_name = serializers.CharField()
    other_party_role = serializers.CharField()
    other_party_subtitle = serializers.CharField(allow_null=True)
    is_open = serializers.BooleanField()


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(allow_null=True)
    sender_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    maps_url = serializers.SerializerMethodField()
    map_preview_url = serializers.SerializerMethodField()

    class Meta:
        model = BookingMessage
        fields = [
            'id', 'message_type', 'sender_id', 'sender_name', 'sender_role',
            'body', 'metadata', 'maps_url', 'map_preview_url', 'created_at', 'is_own', 'is_read',
        ]
        read_only_fields = fields

    def get_sender_name(self, obj):
        return sender_display_name(obj.sender)

    def get_sender_role(self, obj):
        return sender_role_label(obj.sender)

    def get_is_own(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.sender_id == request.user.id

    def get_is_read(self, obj):
        read_at = self.context.get('counterparty_read_at')
        if not read_at or not obj.sender_id:
            return False
        request = self.context.get('request')
        if not request or obj.sender_id != request.user.id:
            return False
        return obj.created_at <= read_at

    def get_maps_url(self, obj):
        if obj.message_type != BookingMessage.MessageType.LOCATION or not obj.metadata:
            return None
        lat = obj.metadata.get('latitude')
        lng = obj.metadata.get('longitude')
        if lat is None or lng is None:
            return None
        return f'https://www.google.com/maps?q={lat},{lng}'

    def get_map_preview_url(self, obj):
        if obj.message_type != BookingMessage.MessageType.LOCATION or not obj.metadata:
            return None
        lat = obj.metadata.get('latitude')
        lng = obj.metadata.get('longitude')
        if lat is None or lng is None:
            return None
        request = self.context.get('request')
        return map_preview_absolute_url(lat, lng, request=request)


class SendMessageSerializer(serializers.Serializer):
    message_type = serializers.ChoiceField(
        choices=[BookingMessage.MessageType.TEXT, BookingMessage.MessageType.LOCATION],
        default=BookingMessage.MessageType.TEXT,
        required=False,
    )
    body = serializers.CharField(max_length=2000, trim_whitespace=True, required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    label = serializers.CharField(max_length=255, required=False, allow_blank=True)
    accuracy = serializers.FloatField(required=False, min_value=0)

    def validate(self, data):
        message_type = data.get('message_type') or BookingMessage.MessageType.TEXT
        if message_type == BookingMessage.MessageType.LOCATION:
            if data.get('latitude') is None or data.get('longitude') is None:
                raise serializers.ValidationError(
                    'latitude and longitude are required for location messages.'
                )
            lat = round(float(data['latitude']), 6)
            lng = round(float(data['longitude']), 6)
            if lat < -90 or lat > 90:
                raise serializers.ValidationError({'latitude': 'Latitude must be between -90 and 90.'})
            if lng < -180 or lng > 180:
                raise serializers.ValidationError({'longitude': 'Longitude must be between -180 and 180.'})
            data['latitude'] = lat
            data['longitude'] = lng
            data['body'] = (data.get('label') or data.get('body') or 'Current location').strip()
            return data

        body = (data.get('body') or '').strip()
        if not body:
            raise serializers.ValidationError({'body': 'Message cannot be empty.'})
        data['body'] = body
        return data
