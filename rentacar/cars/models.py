from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from .enums import CarCategory, CarType, DEFAULT_CATEGORY, validate_category_type_pair


class Car(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cars')
    brand = models.CharField(max_length=100, db_index=True)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    category = models.CharField(
        max_length=20,
        choices=CarCategory.choices,
        default=DEFAULT_CATEGORY,
        db_index=True,
    )
    car_type = models.CharField(max_length=30, choices=CarType.choices, db_index=True)
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

    def clean(self):
        super().clean()
        err = validate_category_type_pair(self.category, self.car_type)
        if err:
            from django.core.exceptions import ValidationError
            raise ValidationError({'car_type': err})

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
