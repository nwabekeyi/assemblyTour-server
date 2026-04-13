from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import (
    Registration,
)
from .services import refresh_user_dashboard_stats


@receiver(post_save, sender=Registration)
def update_stats_on_save(sender, instance, **kwargs):
    refresh_user_dashboard_stats(instance.user_id)


@receiver(post_delete, sender=Registration)
def update_stats_on_delete(sender, instance, **kwargs):
    refresh_user_dashboard_stats(instance.user_id)
