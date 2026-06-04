from django.db.models.signals import post_save
from django.dispatch import receiver

from rentacar.caching import invalidate_admin_lists

from .models import OwnerProfile


@receiver(post_save, sender=OwnerProfile)
def owner_profile_cache_invalidation(sender, instance, **kwargs):
    invalidate_admin_lists()
