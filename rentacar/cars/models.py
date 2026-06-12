from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Car(models.Model):
    CAR_TYPE_CHOICES = (
        # Car types
        ('hatchback', 'Hatchback'),
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('muv_mpv', 'MUV/MPV'),
        ('crossover', 'Crossover'),
        ('convertible', 'Convertible'),
        ('coupe', 'Coupe'),
        ('pickup_truck', 'Pickup Truck'),
        # Luxury Car types
        ('luxury_sedan', 'Luxury Sedan'),
        ('luxury_suv', 'Luxury SUV'),
        ('sports_car', 'Sports Car'),
        ('luxury_convertible', 'Luxury Convertible'),
        ('luxury_coupe', 'Luxury Coupe'),
        ('limousine', 'Limousine'),
        ('electric_luxury', 'Electric Luxury'),
        ('luxury_crossover', 'Luxury Crossover'),
        # Loader types
        ('mini_truck', 'Mini Truck'),
        ('pickup_loader', 'Pickup Loader'),
        ('container_truck', 'Container Truck'),
        ('tipper_dumper', 'Tipper/Dumper'),
        ('flatbed_truck', 'Flatbed Truck'),
        ('refrigerated_truck', 'Refrigerated Truck'),
        ('tanker_truck', 'Tanker Truck'),
        ('crane_truck', 'Crane Truck'),
    )
    CATEGORY_CHOICES = (
        ('car', 'Car'),
        ('luxury_car', 'Luxury Car'),
        ('loader', 'Loader'),
    )
    
    CATEGORY_TYPE_MAP = {
        'car': ['hatchback', 'sedan', 'suv', 'muv_mpv', 'crossover', 'convertible', 'coupe', 'pickup_truck'],
        'luxury_car': ['luxury_sedan', 'luxury_suv', 'sports_car', 'luxury_convertible', 'luxury_coupe', 'limousine', 'electric_luxury', 'luxury_crossover'],
        'loader': ['mini_truck', 'pickup_loader', 'container_truck', 'tipper_dumper', 'flatbed_truck', 'refrigerated_truck', 'tanker_truck', 'crane_truck'],
    }

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cars')
    brand = models.CharField(max_length=100, db_index=True)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='car', db_index=True)
    car_type = models.CharField(max_length=30, choices=CAR_TYPE_CHOICES, db_index=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)

    rent_hourly = models.BooleanField(default=False)
    rent_daily = models.BooleanField(default=True)
    rent_weekly = models.BooleanField(default=False)
    rent_monthly = models.BooleanField(default=False)

    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_week = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    discount_percentage = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    discounted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_available = models.BooleanField(default=True, db_index=True)
    is_approved = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_approved', 'is_available', 'created_at']),
            models.Index(fields=['car_type', 'is_available']),
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['price_per_day']),
        ]

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

    def enabled_rental_types(self):
        types = []
        if self.rent_hourly:
            types.append('hourly')
        if self.rent_daily:
            types.append('daily')
        if self.rent_weekly:
            types.append('weekly')
        if self.rent_monthly:
            types.append('monthly')
        return types

    def get_final_price(self):
        if not self.price_per_day:
            return None
        if self.discounted_price is not None:
            return self.discounted_price
        if self.discount_percentage is not None:
            discount_amount = (self.price_per_day * Decimal(self.discount_percentage)) / Decimal(100)
            return (self.price_per_day - discount_amount).quantize(Decimal('0.01'))
        return self.price_per_day

    @property
    def final_price(self):
        return self.get_final_price()

    @property
    def has_discount(self):
        return (self.discount_percentage is not None and self.discount_percentage > 0) or (self.discounted_price is not None)


class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_images/')
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['car', 'is_primary', 'id']),
        ]

    def __str__(self):
        return f"Image for {self.car}"
