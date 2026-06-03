from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import Booking, Review
from .pricing import (
    compute_total,
    normalize_booking_window,
    validate_rental_window,
    duration_label,
    format_period,
)
from cars.models import Car
from cars.serializers import CarListSerializer
from accounts.serializers import UserSerializer


def _booking_overlap_queryset(car, start_at, end_at):
    return Booking.objects.filter(
        car=car,
        status__in=['pending', 'approved'],
    ).exclude(
        end_at__lte=start_at,
    ).exclude(
        start_at__gte=end_at,
    )


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'car', 'rental_type', 'start_at', 'end_at', 'note']
        read_only_fields = ['id']

    def validate(self, data):
        car = data.get('car')
        rental_type = data.get('rental_type')
        start_at = data.get('start_at')
        end_at = data.get('end_at')

        if start_at and timezone.is_naive(start_at):
            start_at = timezone.make_aware(start_at)
            data['start_at'] = start_at
        if end_at and timezone.is_naive(end_at):
            end_at = timezone.make_aware(end_at)
            data['end_at'] = end_at

        err = validate_rental_window(car, rental_type, start_at, end_at)
        if err:
            raise serializers.ValidationError(err)

        if not car.is_available:
            raise serializers.ValidationError({'car': 'This car is not available for rent.'})

        if not car.is_approved:
            raise serializers.ValidationError({'car': 'This car is not approved yet.'})

        norm_start, norm_end = normalize_booking_window(rental_type, start_at, end_at)
        data['start_at'] = norm_start
        data['end_at'] = norm_end

        if _booking_overlap_queryset(car, norm_start, norm_end).exists():
            raise serializers.ValidationError(
                {'car': 'This car is already booked for the selected period.'}
            )
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        car = validated_data['car']
        rental_type = validated_data['rental_type']
        start_at = validated_data['start_at']
        end_at = validated_data['end_at']

        with transaction.atomic():
            car = Car.objects.select_for_update().get(pk=car.pk)
            if not car.is_available:
                raise serializers.ValidationError({'car': 'This car is not available for rent.'})
            if not car.is_approved:
                raise serializers.ValidationError({'car': 'This car is not approved yet.'})

            err = validate_rental_window(car, rental_type, start_at, end_at)
            if err:
                raise serializers.ValidationError(err)

            norm_start, norm_end = normalize_booking_window(rental_type, start_at, end_at)
            if _booking_overlap_queryset(car, norm_start, norm_end).exists():
                raise serializers.ValidationError(
                    {'car': 'This car is already booked for the selected period.'}
                )

            total = compute_total(car, rental_type, norm_start, norm_end)
            return Booking.objects.create(
                customer=request.user,
                car=car,
                rental_type=rental_type,
                start_at=norm_start,
                end_at=norm_end,
                note=validated_data.get('note', ''),
                total_cost=total,
            )


class BookingDetailSerializer(serializers.ModelSerializer):
    car = CarListSerializer(read_only=True)
    customer = UserSerializer(read_only=True)
    duration_label = serializers.SerializerMethodField()
    period_display = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'customer', 'car', 'rental_type', 'start_at', 'end_at',
            'duration_label', 'period_display', 'total_cost', 'status', 'note',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_duration_label(self, obj):
        return duration_label(obj.rental_type, obj.start_at, obj.end_at)

    def get_period_display(self, obj):
        return format_period(obj.rental_type, obj.start_at, obj.end_at)


class BookingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
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
        model = Review
        fields = ['id', 'booking', 'reviewer', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'reviewer', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        booking = data.get('booking')
        request = self.context.get('request')

        if booking.customer != request.user:
            raise serializers.ValidationError("You can only review your own bookings.")

        if booking.status != 'completed':
            raise serializers.ValidationError("You can only review completed bookings.")

        if Review.objects.filter(booking=booking).exists():
            raise serializers.ValidationError("You have already reviewed this booking.")
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['reviewer'] = request.user
        return super().create(validated_data)
