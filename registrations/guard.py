from .models import StepReviewStatus


def can_user_proceed(registration) -> bool:
    """
    User can proceed only if current step is approved.
    """
    review = registration.step_reviews.filter(
        step=registration.current_step
    ).first()

    return review and review.status == StepReviewStatus.APPROVED
