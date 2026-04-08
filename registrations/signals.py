from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import (
    HajjRegistration,
    RegistrationStep,
    RegistrationStepReview,
)
from .services import refresh_user_dashboard_stats


@receiver(post_save, sender=HajjRegistration)
def create_step_reviews(sender, instance, created, **kwargs):
    """
    When a registration is created, generate a review record
    for every active registration step.
    """
    if not created:
        return

    steps = RegistrationStep.objects.filter(is_active=True)

    for step in steps:
        RegistrationStepReview.objects.get_or_create(
            registration=instance,
            step=step,
        )


@receiver(post_save, sender=HajjRegistration)
def update_stats_on_save(sender, instance, **kwargs):
    refresh_user_dashboard_stats(instance.user_id)


@receiver(post_delete, sender=HajjRegistration)
def update_stats_on_delete(sender, instance, **kwargs):
    refresh_user_dashboard_stats(instance.user_id)
