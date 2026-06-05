from django.db import models
from django.conf import settings
from cars.models import Car
from .pricing import (
    RENTAL_TYPE_CHOICES,
    RENTAL_DAILY,
    compute_total,
    duration_label,
)

# Create your models here.


class Booking(models.Model):

    STATUS_CHOICES = (
        ('pending',   'Pending'),
        ('approved',  'Approved'),
        ('rejected',  'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings'
    )
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')
    rental_type = models.CharField(max_length=20, choices=RENTAL_TYPE_CHOICES, default=RENTAL_DAILY)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.id} — {self.customer.username} → {self.car}"

    def calculate_total(self):
        if self.start_at and self.end_at and self.car_id:
            self.total_cost = compute_total(
                self.car, self.rental_type, self.start_at, self.end_at
            )
        return self.total_cost

    def get_duration_label(self):
        return duration_label(self.rental_type, self.start_at, self.end_at)


class Review(models.Model):

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for Booking #{self.booking.id} — {self.rating} stars"
