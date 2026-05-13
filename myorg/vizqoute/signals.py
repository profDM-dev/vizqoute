from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import VizqouteUser


@receiver(post_save, sender=User)
def ensure_vizqoute_profile(sender, instance: User, created: bool, **kwargs):
    """
    Keep a VizqouteUser profile for every auth user.
    This prevents "logged in but no profile" edge cases when users
    are created via Django admin or scripts.
    """
    if not created:
        return

    VizqouteUser.objects.get_or_create(
        user=instance,
        defaults={
            "name": instance.get_full_name() or instance.username,
            "role": "contractor",
            "phone": "-",
        },
    )

