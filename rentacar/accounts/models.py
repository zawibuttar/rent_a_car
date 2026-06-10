from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=20, choices=Role.choices)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER
    
    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_platform_admin(self):
        return self.is_admin


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    national_id_number = models.CharField(max_length=50, blank=True, null=True)
    driving_license_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}'s Customer Profile"


class OwnerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owner_profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    national_id_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s Owner Profile"


class SocialMediaLink(models.Model):
    platform_name = models.CharField(max_length=50)
    url = models.URLField(max_length=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['platform_name', 'created_at']

    def __str__(self):
        return f"{self.platform_name} ({'active' if self.is_active else 'inactive'})"

    @property
    def name(self):
        return self.platform_name

    @property
    def icon(self):
        # Normalize name for lookup
        key = (self.platform_name or '').lower().strip()
        if 'facebook' in key:
            return 'ti ti-brand-facebook'
        elif 'instagram' in key:
            return 'ti ti-brand-instagram'
        elif 'twitter' in key or key == 'x' or 'twitter/x' in key:
            return 'ti ti-brand-x'
        elif 'linkedin' in key:
            return 'ti ti-brand-linkedin'
        elif 'youtube' in key:
            return 'ti ti-brand-youtube'
        elif 'tiktok' in key:
            return 'ti ti-brand-tiktok'
        elif 'pinterest' in key:
            return 'ti ti-brand-pinterest'
        elif 'whatsapp' in key:
            return 'ti ti-brand-whatsapp'
        else:
            return 'ti ti-share'  # Fallback icon