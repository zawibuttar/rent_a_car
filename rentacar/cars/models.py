from django.db import models
from django.conf import settings

# Create your models here.

class Car(models.Model):
    CAR_TYPE_CHOICES = (
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('luxury', 'Luxury'),
        ('hatchback', 'Hatchback'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('wagon', 'Wagon'),
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cars')
    brand = models.CharField(max_length=100, db_index=True)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    car_type = models.CharField(max_length=20, choices=CAR_TYPE_CHOICES, db_index=True)
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

    is_available = models.BooleanField(default=True, db_index=True)
    is_approved = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_approved', 'is_available', 'created_at']),
            models.Index(fields=['car_type', 'is_available']),
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
