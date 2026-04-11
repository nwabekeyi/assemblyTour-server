from datetime import timedelta
import logging
import threading

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import (
    HajjRegistration,
    RegistrationStatus,
    RegistrationStep,
    StepReviewStatus,
    RegistrationStepReview,
    JourneyPresenceStatus,
    UserDashboardStats,
)

logger = logging.getLogger(__name__)


User = get_user_model()


def ensure_registration_status_consistency(registration, total_active_steps=None):
    if total_active_steps is None:
        total_active_steps = RegistrationStep.objects.filter(is_active=True).count()

    if total_active_steps == 0:
        return registration.status

    completed_active_steps = registration.completed_steps.filter(is_active=True).count()

    desired_status = registration.status

    if registration.journey_presence_status == JourneyPresenceStatus.DID_NOT_ARRIVE:
        desired_status = RegistrationStatus.FAILED
    elif registration.journey_presence_status == JourneyPresenceStatus.ARRIVED:
        desired_status = RegistrationStatus.COMPLETED
    elif completed_active_steps >= total_active_steps:
        desired_status = RegistrationStatus.COMPLETED
    else:
        if registration.status == RegistrationStatus.COMPLETED:
            desired_status = RegistrationStatus.PENDING
        elif registration.status == RegistrationStatus.NOT_STARTED and completed_active_steps > 0:
            desired_status = RegistrationStatus.PENDING

    if desired_status != registration.status:
        registration.status = desired_status
        registration.save(update_fields=["status", "updated_at"])

    return registration.status


def _aggregate_user_stats(user_id):
    registrations = HajjRegistration.objects.filter(user_id=user_id).prefetch_related('completed_steps', 'current_step')
    total = registrations.count()
    total_active_steps = RegistrationStep.objects.filter(is_active=True).count()

    completed = failed = in_progress = 0

    for registration in registrations:
        current_status = ensure_registration_status_consistency(registration, total_active_steps)
        if current_status == RegistrationStatus.FAILED:
            failed += 1
        elif current_status == RegistrationStatus.COMPLETED:
            completed += 1
        else:
            in_progress += 1

    return total, in_progress, completed, failed


def refresh_user_dashboard_stats(user_id):
    if not user_id:
        return None

    with transaction.atomic():
        stats, _ = UserDashboardStats.objects.select_for_update().get_or_create(user_id=user_id)
        total, in_progress, completed, failed = _aggregate_user_stats(user_id)
        stats.total_travels = total
        stats.in_progress_travels = in_progress
        stats.completed_travels = completed
        stats.failed_travels = failed
        stats.save()
        return stats


def refresh_all_dashboard_stats():
    user_ids = User.objects.filter(hajj_registration__isnull=False).values_list("id", flat=True)
    for user_id in user_ids:
        refresh_user_dashboard_stats(user_id)


def schedule_midnight_refresh():
    now = timezone.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    delay = (tomorrow - now).total_seconds()

    def _job():
        refresh_all_dashboard_stats()
        schedule_midnight_refresh()

    timer = threading.Timer(delay, _job)
    timer.daemon = True
    timer.start()


def complete_travel_documents_step(registration):
    """Mark the travel documents step as completed and advance to the next step."""
    if not registration:
        print("complete_travel_documents_step: registration is None")
        return None

    travel_step = RegistrationStep.objects.filter(code="travel_documents").first()
    if not travel_step:
        print("complete_travel_documents_step: travel_step not found")
        return None

    print(f"complete_travel_documents_step: checking for registration {registration.id}, current_step: {registration.current_step}")

    required_types = ["visa", "ticket", "hotel_voucher"]
    uploaded_docs = registration.travel_documents.all()
    uploaded_types = set(uploaded_docs.values_list("doc_type", flat=True))
    
    print(f"complete_travel_documents_step: uploaded_types: {uploaded_types}")
    
    missing_types = []
    for doc_type in required_types:
        if doc_type not in uploaded_types:
            missing_types.append(doc_type)
    
    if missing_types:
        missing_labels = {
            "visa": "Visa",
            "ticket": "Flight Ticket", 
            "hotel_voucher": "Hotel Voucher"
        }
        print(f"complete_travel_documents_step: missing types: {missing_types}")
        return {"error": True, "missing": [missing_labels.get(t, t) for t in missing_types]}

    review, created = RegistrationStepReview.objects.get_or_create(
        registration=registration,
        step=travel_step,
        defaults={
            "status": StepReviewStatus.APPROVED,
            "reviewed_by": None,
            "reviewed_at": timezone.now(),
        }
    )
    if not created and review.status != StepReviewStatus.APPROVED:
        review.status = StepReviewStatus.APPROVED
        review.rejection_reason = ""
        review.reviewed_at = timezone.now()
        review.save(update_fields=["status", "rejection_reason", "reviewed_at"])

    if registration.completed_steps.filter(pk=travel_step.pk).exists():
        print(f"complete_travel_documents_step: travel_step already in completed_steps")
        return travel_step

    registration.completed_steps.add(travel_step)

    next_step = RegistrationStep.objects.filter(
        order__gt=travel_step.order,
        is_active=True
    ).order_by('order').first()

    print(f"complete_travel_documents_step: next_step: {next_step}, current_step: {registration.current_step}, travel_step.order: {travel_step.order}")

    if (
        next_step
        and registration.current_step
        and registration.current_step.order <= travel_step.order
    ):
        registration.current_step = next_step
        print(f"complete_travel_documents_step: Setting current_step to {next_step}")
    else:
        print(f"complete_travel_documents_step: NOT setting current_step. next_step={next_step}, current_step={registration.current_step}")

    registration.save(update_fields=["current_step", "updated_at"])

    return travel_step


def complete_payment_details_step(registration):
    """Mark the payment details step as completed and advance to the next step."""
    if not registration:
        return None

    payment_step = RegistrationStep.objects.filter(code="payment_details").first()
    if not payment_step:
        return None

    # Check if at least one payment detail exists
    has_payment = registration.payment_details.exists()
    
    if not has_payment:
        return {"error": True, "missing": ["Payment Proof"]}

    review, created = RegistrationStepReview.objects.get_or_create(
        registration=registration,
        step=payment_step,
        defaults={
            "status": StepReviewStatus.PENDING,  # Needs admin approval
            "reviewed_by": None,
            "reviewed_at": timezone.now(),
        }
    )
    # For payment, we don't auto-approve - it waits for admin
    # If rejected, we keep the rejection reason
    
    if registration.completed_steps.filter(pk=payment_step.pk).exists():
        return payment_step

    registration.completed_steps.add(payment_step)

    # DO NOT move to next step - wait for admin approval
    
    registration.save(update_fields=["updated_at"])

    return payment_step


def approve_payment_step(registration, admin_user=None):
    """Approve the payment step (called by admin)."""
    if not registration:
        return None

    payment_step = RegistrationStep.objects.filter(code="payment_details").first()
    if not payment_step:
        return None

    review, created = RegistrationStepReview.objects.get_or_create(
        registration=registration,
        step=payment_step,
        defaults={
            "status": StepReviewStatus.APPROVED,
            "reviewed_by": admin_user,
            "reviewed_at": timezone.now(),
        }
    )
    
    if not created:
        review.status = StepReviewStatus.APPROVED
        review.reviewed_by = admin_user
        review.reviewed_at = timezone.now()
        review.rejection_reason = ""
        review.save(update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason"])

    # If payment step is now approved, check if we can move to next step
    if registration.completed_steps.filter(pk=payment_step.pk).exists():
        next_step = RegistrationStep.objects.filter(
            order__gt=payment_step.order,
            is_active=True,
        ).order_by('order').first()

        if (
            next_step
            and registration.current_step
            and registration.current_step.order <= payment_step.order
        ):
            registration.current_step = next_step
            registration.save(update_fields=["current_step", "updated_at"])

    return payment_step


def reject_payment_step(registration, reason, admin_user=None):
    """Reject the payment step (called by admin)."""
    if not registration:
        return None

    payment_step = RegistrationStep.objects.filter(code="payment_details").first()
    if not payment_step:
        return None

    with transaction.atomic():
        review, created = RegistrationStepReview.objects.get_or_create(
            registration=registration,
            step=payment_step,
            defaults={
                "status": StepReviewStatus.REJECTED,
                "reviewed_by": admin_user,
                "reviewed_at": timezone.now(),
                "rejection_reason": reason,
            }
        )
        
        if not created:
            review.status = StepReviewStatus.REJECTED
            review.reviewed_by = admin_user
            review.reviewed_at = timezone.now()
            review.rejection_reason = reason
            review.save(update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason"])

        # If payment was previously completed but now rejected, remove from completed steps
        if registration.completed_steps.filter(pk=payment_step.pk).exists():
            registration.completed_steps.remove(payment_step)
            
            # If current step is beyond payment step, move it back
            if (registration.current_step and 
                registration.current_step.order > payment_step.order):
                registration.current_step = payment_step
                
            registration.save(update_fields=["current_step", "completed_steps", "updated_at"])

    return payment_step


def start_new_registration(user, package):
    """Start a new registration for a user with a new package."""
    if not user or not package:
        return None

    # Return error if user already has an active registration (not completed/failed)
    existing = HajjRegistration.objects.filter(
        user=user
    ).exclude(
        status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]
    ).first()

    if existing:
        return {"error": "active_exists", "registration": existing}

    # Get user's old completed/failed registration to copy details from
    old_registration = HajjRegistration.objects.filter(
        user=user,
        status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]
    ).first()

    # Find the payment_details step to start from (skip account_setup, registration_form, document_upload for returning users)
    payment_step = RegistrationStep.objects.filter(code="payment_details", is_active=True).first()
    if not payment_step:
        # Fall back to first step if payment_details doesn't exist
        payment_step = RegistrationStep.objects.filter(is_active=True).order_by('order').first()
    
    if not payment_step:
        return {"error": "no_steps"}

    with transaction.atomic():
        registration = HajjRegistration.objects.create(
            user=user,
            package=package,
            current_step=payment_step,
            status=RegistrationStatus.PENDING,
        )
        
        # Copy documents from old registration if exists
        if old_registration:
            registration.passport_document = old_registration.passport_document
            registration.passport_document_public_id = old_registration.passport_document_public_id
            registration.yellow_card_document = old_registration.yellow_card_document
            registration.yellow_card_document_public_id = old_registration.yellow_card_document_public_id
            registration.save(update_fields=['passport_document', 'passport_document_public_id', 'yellow_card_document', 'yellow_card_document_public_id'])
            
            # Copy completed steps from old registration (except document_upload which we'll re-do)
            old_completed = old_registration.completed_steps.exclude(code__in=['document_upload'])
            for step in old_completed:
                registration.completed_steps.add(step)

    return registration
