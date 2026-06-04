from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from .models import Car, CarImage
from accounts.serializers import UserSerializer
from rentacar.image_validation import validate_car_image_file

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


class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image', 'is_primary', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class CarListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    enabled_rental_types = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'year', 'car_type', 'location', 'is_available',
            'primary_image', 'owner_name',
            'rent_hourly', 'rent_daily', 'rent_weekly', 'rent_monthly',
            'price_per_hour', 'price_per_day', 'price_per_week', 'price_per_month',
            'enabled_rental_types',
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


class AdminCarListSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'year', 'car_type', 'price_per_day',
            'location', 'is_available', 'is_approved', 'owner',
            'rent_hourly', 'rent_daily', 'rent_weekly', 'rent_monthly',
        ]

    def get_owner(self, obj):
        return {'username': obj.owner.username}


class CarDetailSerializer(serializers.ModelSerializer):
    images = CarImageSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    enabled_rental_types = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            'id', 'owner', 'brand', 'model', 'year', 'car_type', 'description', 'location',
            'rent_hourly', 'rent_daily', 'rent_weekly', 'rent_monthly',
            'price_per_hour', 'price_per_day', 'price_per_week', 'price_per_month',
            'enabled_rental_types', 'is_available', 'is_approved', 'images',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'is_approved', 'created_at', 'updated_at']

    def get_enabled_rental_types(self, obj):
        return obj.enabled_rental_types()


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
