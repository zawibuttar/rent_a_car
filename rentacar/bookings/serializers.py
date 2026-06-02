from rest_framework import serializers
from django.utils import timezone
from .models import *
from cars.serializers import CarListSerializer
from accounts.serializers import UserSerializer


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Booking
        fields = ['id', 'car', 'start_date', 'end_date', 'note']
        read_only_fields = ['id']

    def validate(self, data):
        car        = data.get('car')
        start_date = data.get('start_date')
        end_date   = data.get('end_date')
        today      = timezone.now().date()

        if start_date < today:
            raise serializers.ValidationError({"start_date": "Start date cannot be in the past."})

        if end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})

        days = (end_date - start_date).days
        if days < 1:
            raise serializers.ValidationError("Minimum booking is 1 day.")

        if not car.is_available:
            raise serializers.ValidationError({"car": "This car is not available for rent."})

        if not car.is_approved:
            raise serializers.ValidationError({"car": "This car is not approved yet."})

        overlapping = Booking.objects.filter(
            car=car, status__in=['pending', 'approved'],
        ).exclude(
            end_date__lte=start_date   
        ).exclude(
            start_date__gte=end_date  
        )

        if overlapping.exists():
            raise serializers.ValidationError({"car": "This car is already booked for the selected dates."})
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['customer'] = request.user
        car        = validated_data['car']
        start_date = validated_data['start_date']
        end_date   = validated_data['end_date']
        days       = (end_date - start_date).days
        validated_data['total_cost'] = days * car.price_per_day
        return super().create(validated_data)


class BookingDetailSerializer(serializers.ModelSerializer):
    car      = CarListSerializer(read_only=True)
    customer = UserSerializer(read_only=True)

    class Meta:
        model  = Booking
        fields = ['id', 'customer', 'car', 'start_date', 'end_date', 'total_cost', 'status', 'note', 'created_at', 'updated_at']
        read_only_fields = fields


class BookingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Booking
        fields = ['id', 'status']

    def validate_status(self, value):
        allowed = ['approved', 'rejected']
        if value not in allowed:
            raise serializers.ValidationError(
                f"Owner can only set status to: {', '.join(allowed)}"
            )
        return value


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model  = Review
        fields = ['id', 'booking', 'reviewer', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'reviewer', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        booking  = data.get('booking')
        request  = self.context.get('request')

        if booking.customer != request.user:
            raise serializers.ValidationError("You can only review your own bookings.")

        if booking.status != 'completed':
            raise serializers.ValidationError("You can only review completed bookings.")

        # Use exists() instead of filter().exists() to avoid extra query
        if Review.objects.filter(booking=booking).exists():
            raise serializers.ValidationError("You have already reviewed this booking.")
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['reviewer'] = request.user
        return super().create(validated_data)