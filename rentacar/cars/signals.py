from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from rentacar.caching import invalidate_car_caches

from .models import Car, CarImage


@receiver(post_save, sender=Car)
@receiver(post_delete, sender=Car)
def car_cache_invalidation(sender, instance, **kwargs):
    invalidate_car_caches()


@receiver(post_save, sender=CarImage)
@receiver(post_delete, sender=CarImage)
def car_image_cache_invalidation(sender, instance, **kwargs):
    invalidate_car_caches()
