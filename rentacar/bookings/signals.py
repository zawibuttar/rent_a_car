from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from rentacar.caching import invalidate_booking_caches, invalidate_public_car_lists

from .models import Booking


@receiver(post_save, sender=Booking)
@receiver(post_delete, sender=Booking)
def booking_cache_invalidation(sender, instance, **kwargs):
    owner_id = instance.car.owner_id if instance.car_id else None
    invalidate_booking_caches(
        user_id=instance.customer_id,
        owner_id=owner_id,
    )
    invalidate_public_car_lists()
