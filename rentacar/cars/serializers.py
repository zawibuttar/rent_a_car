from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from bookings.models import Review
from .models import Car, CarImage
from .booking_availability import car_booking_availability
from .review_stats import get_car_review_summary, get_car_reviews
from accounts.serializers import UserSerializer
from rentacar.image_validation import validate_car_image_file
from rentacar.utils import format_display_name


class CarReviewPublicSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'created_at', 'reviewer_name']
        read_only_fields = fields

    def get_reviewer_name(self, obj):
        if not obj.reviewer_id:
            return ''
        return format_display_name(obj.reviewer.username)

RENTAL_TYPE_META = (
    ('hourly', 'rent_hourly', 'price_per_hour'),
    ('daily', 'rent_daily', 'price_per_day'),
    ('weekly', 'rent_weekly', 'price_per_week'),
    ('monthly', 'rent_monthly', 'price_per_month'),
)


def validate_car_rental_options(data):
    """Validate enabled rental types and matching prices. Mutates nothing."""
    errors = {}
    enabled = []
    for _type, flag, price_field in RENTAL_TYPE_META:
        if data.get(flag):
            enabled.append(_type)
            price = data.get(price_field)
            if price is None or price <= 0:
                errors[price_field] = f'Price is required when {_type} rental is enabled.'

    if not enabled:
        errors['non_field_errors'] = 'Enable at least one rental type (hourly, daily, weekly, or monthly).'

    if data.get('rent_daily') and (data.get('price_per_day') is None or data.get('price_per_day') <= 0):
        errors['price_per_day'] = 'Price per day is required when daily rental is enabled.'

    if errors:
        raise serializers.ValidationError(errors)
    return data


class BookedSlotsMixin:
    """Shared booked_slots / is_currently_booked for car serializers."""

    booked_slots_limit = 3

    def _booked_slots_context(self, obj):
        cache = getattr(self, '_booked_slots_cache', None)
        if cache is None:
            cache = {}
            self._booked_slots_cache = cache
        if obj.pk not in cache:
            limit = getattr(self, 'booked_slots_limit', 3)
            slots, total, is_currently_booked = car_booking_availability(
                obj, limit=limit
            )
            cache[obj.pk] = {
                'booked_slots': slots,
                'booked_slots_total': total,
                'is_currently_booked': is_currently_booked,
            }
        return cache[obj.pk]

    def get_booked_slots(self, obj):
        return self._booked_slots_context(obj)['booked_slots']

    def get_booked_slots_total(self, obj):
        return self._booked_slots_context(obj)['booked_slots_total']

    def get_is_currently_booked(self, obj):
        return self._booked_slots_context(obj)['is_currently_booked']


class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image', 'is_primary', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class CarListSerializer(BookedSlotsMixin, serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    enabled_rental_types = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    booked_slots = serializers.SerializerMethodField()
    booked_slots_total = serializers.SerializerMethodField()
    is_currently_booked = serializers.SerializerMethodField()
    booked_slots_limit = 3

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'year', 'car_type', 'location', 'is_available',
            'primary_image', 'owner_name',
            'rent_hourly', 'rent_daily', 'rent_weekly', 'rent_monthly',
            'price_per_hour', 'price_per_day', 'price_per_week', 'price_per_month',
            'enabled_rental_types',
            'review_count', 'average_rating',
            'booked_slots', 'booked_slots_total', 'is_currently_booked',
        ]

    def get_primary_image(self, obj):
        image_path = getattr(obj, 'primary_image', None)
        if image_path:
            full_path = settings.MEDIA_URL + image_path.lstrip('/')
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(full_path)
            return full_path

        if hasattr(obj, '_prefetched_objects_cache') and 'images' in obj._prefetched_objects_cache:
            images = list(obj.images.all())
            image = next((img for img in images if img.is_primary), None)
            if not image and images:
                image = images[0]
            if image and image.image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(image.image.url)
        return None

    def get_enabled_rental_types(self, obj):
        return obj.enabled_rental_types()

    def get_owner_name(self, obj):
        if not obj.owner_id:
            return ''
        return format_display_name(obj.owner.username)

    def get_review_count(self, obj):
        return getattr(obj, 'review_count', 0) or 0

    def get_average_rating(self, obj):
        avg = getattr(obj, 'average_rating', None)
        if avg is None:
            return None
        return round(float(avg), 1)


class AdminCarListSerializer(BookedSlotsMixin, serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    booked_slots = serializers.SerializerMethodField()
    booked_slots_total = serializers.SerializerMethodField()
    is_currently_booked = serializers.SerializerMethodField()
    booked_slots_limit = 3

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'year', 'car_type', 'price_per_day',
            'location', 'is_available', 'is_approved', 'owner',
            'rent_hourly', 'rent_daily', 'rent_weekly', 'rent_monthly',
            'booked_slots', 'booked_slots_total', 'is_currently_booked',
        ]

    def get_owner(self, obj):
        return {
            'username': obj.owner.username,
            'display_name': format_display_name(obj.owner.username),
        }


class CarDetailSerializer(BookedSlotsMixin, serializers.ModelSerializer):
    images = CarImageSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    enabled_rental_types = serializers.SerializerMethodField()
    booked_slots = serializers.SerializerMethodField()
    booked_slots_total = serializers.SerializerMethodField()
    is_currently_booked = serializers.SerializerMethodField()
    booked_slots_limit = 15

    class Meta:
        model = Car
        fields = [
            'id', 'owner', 'brand', 'model', 'year', 'car_type', 'description', 'location',
            'rent_hourly', 'rent_daily', 'rent_weekly', 'rent_monthly',
            'price_per_hour', 'price_per_day', 'price_per_week', 'price_per_month',
            'enabled_rental_types', 'is_available', 'is_approved', 'images',
            'review_summary', 'reviews',
            'booked_slots', 'booked_slots_total', 'is_currently_booked',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'is_approved', 'created_at', 'updated_at']

    review_summary = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    def get_enabled_rental_types(self, obj):
        return obj.enabled_rental_types()

    def get_review_summary(self, obj):
        return get_car_review_summary(obj)

    def get_reviews(self, obj):
        qs = get_car_reviews(obj, limit=20)
        return CarReviewPublicSerializer(qs, many=True, context=self.context).data


class CarCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'year', 'car_type', 'description', 'location',
            'rent_hourly', 'rent_daily', 'rent_weekly', 'rent_monthly',
            'price_per_hour', 'price_per_day', 'price_per_week', 'price_per_month',
            'is_available',
        ]
        read_only_fields = ['id']

    def validate_year(self, value):
        max_year = timezone.now().year + 1
        if value < 1990 or value > max_year:
            raise serializers.ValidationError(
                f"Year must be between 1990 and {max_year}."
            )
        return value

    def validate(self, data):
        instance = getattr(self, 'instance', None)
        merged = {}
        for _type, flag, price_field in RENTAL_TYPE_META:
            merged[flag] = data.get(flag, getattr(instance, flag, False) if instance else False)
            merged[price_field] = data.get(
                price_field,
                getattr(instance, price_field, None) if instance else None,
            )
        validate_car_rental_options(merged)
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['owner'] = request.user
        validated_data.setdefault('is_approved', True)
        if validated_data.get('rent_daily') and not validated_data.get('price_per_day'):
            raise serializers.ValidationError({'price_per_day': 'Required for daily rental.'})
        return super().create(validated_data)


class CarImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image', 'is_primary']
        read_only_fields = ['id']

    def validate_image(self, value):
        err = validate_car_image_file(value)
        if err:
            raise serializers.ValidationError(err)
        return value
