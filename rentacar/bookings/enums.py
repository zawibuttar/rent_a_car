"""
Rental duration — how long a customer books a vehicle (not vehicle category/type).
"""
from django.db import models


class RentalDuration(models.TextChoices):
    HOURLY = 'hourly', 'Hourly'
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'
