from django.conf import settings
from rest_framework import serializers
from .models import *
from accounts.serializers import UserSerializer

class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image', 'is_primary', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class CarListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Car
        fields = ['id', 'brand', 'model', 'year', 'car_type', 'price_per_day', 'location', 'is_available', 'primary_image', 'owner_name']

    def get_primary_image(self, obj):
        # Check for annotated primary_image first (from queryset)
        image_path = getattr(obj, 'primary_image', None)
        if image_path:
            full_path = settings.MEDIA_URL + image_path.lstrip('/')
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(full_path)
            return full_path

        # Fallback: Check prefetched images if annotation not available
        # This is safe because CarListView uses prefetch_related('images')
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


class CarDetailSerializer(serializers.ModelSerializer):
    images = CarImageSerializer(many=True, read_only=True)
    owner  = UserSerializer(read_only=True)

    class Meta:
        model  = Car
        fields = ['id', 'owner', 'brand', 'model', 'year', 'car_type', 'description', 'location', 'price_per_day', 'is_available', 'is_approved', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'is_approved', 'created_at', 'updated_at']


class CarCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Car
        fields = ['id', 'brand', 'model', 'year', 'car_type','description', 'location', 'price_per_day', 'is_available']
        read_only_fields = ['id']

    def validate_year(self, value):
        if value < 1990 or value > 2026:
            raise serializers.ValidationError("Year must be between 1990 and 2026.")
        return value

    def validate_price_per_day(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price per day must be greater than zero.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['owner'] = request.user
        return super().create(validated_data)


class CarImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CarImage
        fields = ['id', 'image', 'is_primary']
        read_only_fields = ['id']