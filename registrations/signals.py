from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    HajjRegistration,
    RegistrationStep,
    RegistrationStepReview,
)


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
