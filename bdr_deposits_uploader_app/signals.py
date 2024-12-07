"""
Implements signals for the bdr_deposits_uploader_app.
Enables auto-creation of a UserProfile record when a new User record is created.
See the README for more info.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from bdr_deposits_uploader_app.models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)
        instance.userprofile.save()
