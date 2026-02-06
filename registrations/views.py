from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    HajjRegistration,
    RegistrationStep,
    RegistrationStatus,
    StepReviewStatus,
    RegistrationStepReview,
)
from .serializers import (
    UserHajjRegistrationSerializer,
    AccountSetupSerializer,
    RegistrationFormSerializer,
    DocumentUploadSerializer
)
from core.utils.api_response import api_response

User = get_user_model()

def can_user_proceed(registration) -> bool:
    """
    User can proceed only if current step is approved.
    If the step doesn't require approval, they can proceed.
    """
    if registration.current_step.action_type == "approval":
        review = registration.step_reviews.filter(
            step=registration.current_step
        ).first()
        return review and review.status == StepReviewStatus.APPROVED
    return True


class MyHajjRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            registration = HajjRegistration.objects.select_related(
                'current_step', 'package'
            ).prefetch_related(
                'completed_steps'
            ).get(user=request.user)

            serializer = UserHajjRegistrationSerializer(registration)

            return api_response(
                success=True,
                message="Your hajj registration retrieved successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
            )

        except HajjRegistration.DoesNotExist:
            return api_response(
                success=False,
                message="You have not started a hajj registration yet",
                data=None,
                errors={"registration": "Not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )


# Step 1 – account_setup: Moves forward and auto-approves immediately
class AccountSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            registration = HajjRegistration.objects.select_related(
                'current_step'
            ).get(user=request.user)
        except HajjRegistration.DoesNotExist:
            return api_response(success=False, message="Registration not found", status_code=404)

        if registration.current_step.code != "account_setup":
            return api_response(success=False, message="Invalid step", status_code=400)

        if registration.completed_steps.filter(code="account_setup").exists():
            return api_response(success=False, message="Step already completed", status_code=410)

        serializer = AccountSetupSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return api_response(success=False, message="Validation failed", errors=serializer.errors, status_code=400)

        with transaction.atomic():
            user = request.user
            user.set_password(serializer.validated_data['password'])

            if username := serializer.validated_data.get('username', '').strip():
                if username != user.username:
                    user.username = username
            user.save()

            # --- AUTO-APPROVE STEP 1 ---
            registration.completed_steps.add(registration.current_step)
            
            RegistrationStepReview.objects.update_or_create(
                registration=registration,
                step=registration.current_step,
                defaults={
                    "status": StepReviewStatus.APPROVED,
                    "reviewed_at": timezone.now(),
                    "rejection_reason": None
                }
            )

            # Move to next step (Step 2) automatically
            next_step = RegistrationStep.objects.filter(
                order__gt=registration.current_step.order,
                is_active=True
            ).order_by('order').first()

            if next_step:
                registration.current_step = next_step
            
            registration.save(update_fields=['current_step', 'updated_at'])

        registration.refresh_from_db()
        return api_response(
            success=True,
            message="Account setup completed and approved successfully",
            data=UserHajjRegistrationSerializer(registration).data
        )


# Step 2 – registration_form: Saves to User, creates PENDING Review
class RegistrationFormView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        try:
            registration = HajjRegistration.objects.select_related(
                'current_step'
            ).get(user=request.user)
        except HajjRegistration.DoesNotExist:
            return api_response(
                success=False,
                message="Registration not found",
                status_code=404
            )

        if registration.current_step.code != "registration_form":
            return api_response(
                success=False,
                message="Invalid step",
                status_code=400
            )

        serializer = RegistrationFormSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status_code=400
            )

        email = serializer.validated_data['email']
        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            return api_response(
                success=False,
                message="Validation failed",
                errors={"email": ["A user with this email already exists."]},
                status_code=400
            )

        with transaction.atomic():
            user = request.user

            # ✅ Update existing user fields
            for field, value in serializer.validated_data.items():
                setattr(user, field, value)

            user.save()

            # Ensure step is marked completed
            registration.completed_steps.add(registration.current_step)

            # Reset / create review as PENDING
            RegistrationStepReview.objects.update_or_create(
                registration=registration,
                step=registration.current_step,
                defaults={
                    "status": StepReviewStatus.PENDING,
                    "rejection_reason": None,
                    "reviewed_by": None,
                    "reviewed_at": None
                }
            )

            registration.save(update_fields=["updated_at"])

        registration.refresh_from_db()
        return api_response(
            success=True,
            message="Bio-data updated and submitted for admin review",
            data=UserHajjRegistrationSerializer(registration).data,
            status_code=status.HTTP_200_OK
        )


# --- STEP 3: Updated to save to HajjRegistration ---
class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            registration = HajjRegistration.objects.select_related('current_step').get(user=request.user)
        except HajjRegistration.DoesNotExist:
            return api_response(success=False, message="Registration not found", status_code=404)

        if registration.current_step.code != "document_upload":
            return api_response(success=False, message="Invalid step", status_code=400)

        if not can_user_proceed(registration):
            return api_response(success=False, message="Waiting for approval", status_code=403)

        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(success=False, message="Validation failed", errors=serializer.errors, status_code=400)

        with transaction.atomic():
            # Update HajjRegistration model fields instead of User model
            registration.passport_document = serializer.validated_data['passport']
            registration.yellow_card_document = serializer.validated_data['yellow_card']
            
            registration.completed_steps.add(registration.current_step)

            # Create Review record as PENDING
            RegistrationStepReview.objects.update_or_create(
                registration=registration,
                step=registration.current_step,
                defaults={
                    "status": StepReviewStatus.PENDING,
                    "rejection_reason": None,
                    "reviewed_by": None,
                    "reviewed_at": None
                }
            )

            registration.save(update_fields=['passport_document', 'yellow_card_document', 'updated_at'])

        registration.refresh_from_db()
        return api_response(
            success=True,
            message="Documents uploaded to registration and submitted for review",
            data=UserHajjRegistrationSerializer(registration).data
        )