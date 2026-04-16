from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import (
    Registration,
    RegistrationStep,
    RegistrationStatus,
    StepReviewStatus,
    RegistrationStepReview,
    TravelDocument,
    SupportTicket,
    SupportTicketReply,
    ManasikGuidance,
    EmergencyContact,
    UserDashboardStats,
    PaymentDetail,
)
from .serializers import (
    UserRegistrationSerializer,
    AccountSetupSerializer,
    RegistrationFormSerializer,
    DocumentUploadSerializer,
    TravelDocumentSerializer,
    TravelDocumentUploadSerializer,
    SupportTicketSerializer,
    SupportTicketReplySerializer,
    SupportTicketCreateSerializer,
    ManasikGuidanceSerializer,
    EmergencyContactSerializer,
)
from core.utils.api_response import api_response
from core.services.cloudinary_service import CloudinaryService
from core.services.email_service import notify_admins_of_registration_event
from .services import (
    refresh_user_dashboard_stats, 
    complete_travel_documents_step,
    complete_payment_details_step,
    approve_payment_step,
    reject_payment_step
)

User = get_user_model()


def get_cloudinary_service():
    return CloudinaryService()

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


class MyRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            registration = Registration.objects.select_related(
                'current_step', 'package'
            ).prefetch_related(
                'completed_steps'
            ).exclude(
                status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]
            ).exclude(status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]).get(user=request.user)

            serializer = UserRegistrationSerializer(registration)

            return api_response(
                success=True,
                message="Your hajj registration retrieved successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
            )

        except Registration.DoesNotExist:
            return api_response(
                success=True,
                message="No active registration",
                data=None,
                status_code=status.HTTP_200_OK,
            )


# Step 1 – account_setup: Moves forward and auto-approves immediately
class AccountSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            registration = Registration.objects.select_related(
                'current_step'
            ).exclude(status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]).get(user=request.user)
        except Registration.DoesNotExist:
            return api_response(success=False, message="Registration not found", status_code=404)

        if registration.current_step.code != "account_setup":
            return api_response(success=False, message="Invalid step", status_code=400)

        if registration.completed_steps.filter(code="account_setup").exists():
            return api_response(success=False, message="Step already completed", status_code=410)

        serializer = AccountSetupSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return api_response(success=False, message="Validation failed", errors=serializer.errors, status_code=400)

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
            data=UserRegistrationSerializer(registration).data
        )


# Step 2 – registration_form: Saves to User, creates PENDING Review
class RegistrationFormView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        try:
            registration = Registration.objects.filter(
                user=request.user,
                status__in=['not_started', 'pending', 'in_progress']
            ).select_related('current_step').first()
        except Registration.DoesNotExist:
            return api_response(
                success=False,
                message="Registration not found",
                status_code=404
            )

        if not registration or registration.current_step.code != "registration_form":
            return api_response(
                success=False,
                message="Not at registration form step",
                status_code=400
            )

        user = request.user
        
        user_data = {
            'email': user.email or "",
            'first_name': user.first_name or "",
            'last_name': user.last_name or "",
            'phone': user.phone or "",
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'gender': user.gender or "",
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'nationality': user.nationality or "",
            'state_of_origin': user.state_of_origin or "",
            'passport_number': user.passport_number or "",
            'passport_expiry': user.passport_expiry.isoformat() if user.passport_expiry else None,
            'address': user.address or "",
            'emergency_contact_name': user.emergency_contact_name or "",
            'emergency_contact_phone': user.emergency_contact_phone or "",
        }

        return api_response(success=True, data=user_data)

    def patch(self, request):
        try:
            registration = Registration.objects.select_related(
                'current_step'
            ).exclude(status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]).get(user=request.user)
        except Registration.DoesNotExist:
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

        user = request.user
        
        # Get all data from request
        data = request.data.copy()
        
        # Remove empty strings from data
        for key in list(data.keys()):
            if data.get(key) == '' or data.get(key) is None:
                data.pop(key, None)
        
        # If no data left after removing empties, require all fields
        if not data and not request.data.get('profile_picture'):
            return api_response(
                success=False,
                message="Please fill in your information",
                errors={"form": ["Please provide your details"]},
                status_code=400
            )
        
        serializer = RegistrationFormSerializer(data=data, partial=True)
        if not serializer.is_valid():
            return api_response(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status_code=400
            )

        # Validate email uniqueness only if email is being changed
        email = serializer.validated_data.get('email')
        if email and User.objects.filter(email=email).exclude(id=request.user.id).exists():
            return api_response(
                success=False,
                message="Validation failed",
                errors={"email": ["A user with this email already exists."]},
                status_code=400
            )

        # Handle profile picture upload to Cloudinary
        profile_pic = serializer.validated_data.get('profile_picture')
            
        if profile_pic:
            try:
                upload_result = get_cloudinary_service().upload(
                    profile_pic,
                    subfolder=f"hajj/users/{request.user.id}"
                )
                user.profile_picture = upload_result.get('secure_url') or upload_result.get('url')
            except Exception as e:
                return api_response(
                    success=False,
                    message="Failed to upload profile picture",
                    errors={"profile_picture": [str(e)]},
                    status_code=400
                )
        
        # Update user fields with validated data
        validated_data = serializer.validated_data.copy()
        
        # Handle profile picture separately (already uploaded above)
        profile_pic_url = validated_data.pop('profile_picture', None)
        if profile_pic_url and not user.profile_picture:
            # Only set if user doesn't have one AND we just uploaded one
            pass  # Already handled above
        
        for field, value in validated_data.items():
            # Only update if user doesn't already have this field filled (optional)
            current_value = getattr(user, field, None)
            if not current_value and value:
                setattr(user, field, value)
        
        user.save()

        # Ensure step is marked completed
        registration.completed_steps.add(registration.current_step)

        # Auto-approve immediately - no admin approval needed for registration form
        RegistrationStepReview.objects.update_or_create(
            registration=registration,
            step=registration.current_step,
            defaults={
                "status": StepReviewStatus.APPROVED,
                "rejection_reason": None,
                "reviewed_by": request.user,
                "reviewed_at": timezone.now()
            }
        )

        # Move to next step (payment_details) immediately
        next_step = RegistrationStep.objects.filter(
            order__gt=registration.current_step.order,
            is_active=True
        ).order_by('order').first()

        if next_step:
            registration.current_step = next_step

        if registration.status == RegistrationStatus.FAILED:
            registration.status = RegistrationStatus.PENDING

        registration.save(update_fields=["current_step", "status", "updated_at"])

        registration.refresh_from_db()
        
        return api_response(
            success=True,
            message="Bio-data updated successfully",
            data=UserRegistrationSerializer(registration).data,
            status_code=status.HTTP_200_OK
        )


# --- STEP 3: Updated to save to Registration ---
class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            registration = Registration.objects.select_related('current_step').exclude(status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]).get(user=request.user)
        except Registration.DoesNotExist:
            return api_response(success=False, message="Registration not found", status_code=404)

        if registration.current_step.code != "document_upload":
            return api_response(success=False, message="Invalid step", status_code=400)

        if not can_user_proceed(registration):
            return api_response(success=False, message="Waiting for approval", status_code=403)

        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(success=False, message="Validation failed", errors=serializer.errors, status_code=400)

        passport_file = serializer.validated_data['passport']
        yellow_card_file = serializer.validated_data['yellow_card']

        folder = f"hajj/registrations/{registration.id}/documents"
        try:
            passport_upload = get_cloudinary_service().upload(passport_file, subfolder=folder)
            yellow_card_upload = get_cloudinary_service().upload(yellow_card_file, subfolder=folder)
        except Exception as exc:
            return api_response(
                success=False,
                message="Failed to upload documents to Cloudinary",
                errors={"detail": [str(exc)]},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        old_passport_public_id = registration.passport_document_public_id
        old_yellow_public_id = registration.yellow_card_document_public_id

        registration.passport_document = passport_upload.get('secure_url') or passport_upload.get('url')
        registration.passport_document_public_id = passport_upload.get('public_id')
        registration.yellow_card_document = yellow_card_upload.get('secure_url') or yellow_card_upload.get('url')
        registration.yellow_card_document_public_id = yellow_card_upload.get('public_id')

        registration.completed_steps.add(registration.current_step)

        # Create review as PENDING - wait for admin approval
        step = registration.current_step
        RegistrationStepReview.objects.update_or_create(
            registration=registration,
            step=step,
            defaults={
                "status": StepReviewStatus.PENDING,
                "rejection_reason": None,
                "reviewed_by": None,
                "reviewed_at": None
            }
        )

        # DO NOT move to next step - wait for admin approval
        registration.save(update_fields=[
            'passport_document',
            'passport_document_public_id',
            'yellow_card_document',
            'yellow_card_document_public_id',
            'updated_at'
        ])

        # Clean up old assets after successful save
        if old_passport_public_id and old_passport_public_id != registration.passport_document_public_id:
            try:
                get_cloudinary_service().delete(old_passport_public_id)
            except Exception:
                pass

        if old_yellow_public_id and old_yellow_public_id != registration.yellow_card_document_public_id:
            try:
                get_cloudinary_service().delete(old_yellow_public_id)
            except Exception:
                pass

        registration.refresh_from_db()
        
        # Notify admins
        try:
            user_name = f"{request.user.first_name or ''} {request.user.last_name or ''}".strip() or request.user.username or request.user.email
            admin_emails = list(User.objects.filter(can_approve_registrations=True, is_active=True, email__isnull=False).values_list('email', flat=True))
            if admin_emails:
                notify_admins_of_registration_event(admin_emails, 'document_upload', user_name, registration.id)
        except Exception:
            pass
        
        return api_response(
            success=True,
            message="Documents uploaded. Please wait for admin review.",
            data=UserRegistrationSerializer(registration).data
        )


# -----------------------------
# ADMIN: Approve/Reject Step 3 (Document Review)
# -----------------------------
class AdminApproveDocumentReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def post(self, request, registration_id):
        if not self._is_admin(request.user):
            return api_response(success=False, message="Admin only", status_code=403)

        action = request.data.get("action")
        reason = request.data.get("reason", "").strip()

        if action not in ["approve", "reject"]:
            return api_response(success=False, message="Invalid action", status_code=400)

        try:
            registration = Registration.objects.select_related('current_step', 'user').get(id=registration_id)
        except Registration.DoesNotExist:
            return api_response(success=False, message="Registration not found", status_code=404)

        if registration.current_step.code != "document_upload":
            return api_response(success=False, message="Registration not at document upload step", status_code=400)

        step = registration.current_step

        review, _ = RegistrationStepReview.objects.get_or_create(
            registration=registration,
            step=step,
            defaults={"reviewed_by": request.user}
        )

        if action == "approve":
            review.approve(request.user)
            if registration.status == RegistrationStatus.FAILED:
                registration.status = RegistrationStatus.PENDING
            registration.completed_steps.add(step)

            next_step = RegistrationStep.objects.filter(
                order__gt=step.order,
                is_active=True
            ).order_by('order').first()

            if next_step:
                registration.current_step = next_step

            registration.save(update_fields=['status', 'current_step', 'updated_at'])
            message = "Documents approved. Registration moved to next step."

            # Send approval email (non-blocking)
            try:
                from core.services.email_service import send_step_approved_email
                if registration.user.email:
                    send_step_approved_email(registration.user.email, step.title, registration.id)
            except Exception:
                pass  # Don't crash if email fails

        else:
                if not reason:
                    return api_response(success=False, message="Rejection reason required", status_code=400)
                review.reject(request.user, reason)
                registration.status = RegistrationStatus.FAILED
                registration.save(update_fields=['status', 'updated_at'])
                message = f"Documents rejected: {reason}"

                # Send rejection email (non-blocking)
                try:
                    from core.services.email_service import send_step_rejected_email
                    if registration.user.email:
                        send_step_rejected_email(registration.user.email, step.title, registration.id)
                except Exception:
                    pass  # Don't crash if email fails

        registration.refresh_from_db()
        return api_response(
            success=True,
            message=message,
            data=UserRegistrationSerializer(registration).data
        )


# -----------------------------
# ADMIN: Upload Travel Documents for User
# -----------------------------
class AdminUploadTravelDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def post(self, request, registration_id):
        if not self._is_admin(request.user):
            return api_response(success=False, message="Admin only", status_code=403)

        try:
            registration = Registration.objects.get(id=registration_id)
        except Registration.DoesNotExist:
            return api_response(success=False, message="Registration not found", status_code=404)

        serializer = TravelDocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(success=False, message="Validation failed", errors=serializer.errors, status_code=400)

        travel_doc = TravelDocument.objects.create(
            registration=registration,
            doc_type=serializer.validated_data['doc_type'],
            title=serializer.validated_data['title'],
            file=serializer.validated_data['file'],
            description=serializer.validated_data.get('description', ''),
            uploaded_by=request.user
        )

        import json
        ticket_doc = registration.travel_documents.filter(doc_type='ticket').first()
        hotel_doc = registration.travel_documents.filter(doc_type='hotel_voucher').first()
        
        if ticket_doc:
            ticket_info = {
                "airline_name": ticket_doc.airline_name,
                "flight_number": ticket_doc.flight_number,
                "departure_airport": ticket_doc.departure_airport,
                "arrival_airport": ticket_doc.arrival_airport,
                "departure_date": str(ticket_doc.departure_date) if ticket_doc.departure_date else None,
                "arrival_date": str(ticket_doc.arrival_date) if ticket_doc.arrival_date else None,
                "seat_number": ticket_doc.seat_number,
                "booking_reference": ticket_doc.booking_reference,
            }
            registration.ticket_info = json.dumps(ticket_info)
        
        if hotel_doc:
            hotel_info = {
                "hotel_name": hotel_doc.hotel_name,
                "hotel_address": hotel_doc.hotel_address,
                "room_type": hotel_doc.room_type,
                "room_number": hotel_doc.room_number,
                "check_in_date": str(hotel_doc.check_in_date) if hotel_doc.check_in_date else None,
                "check_out_date": str(hotel_doc.check_out_date) if hotel_doc.check_out_date else None,
                "number_of_nights": hotel_doc.number_of_nights,
            }
            registration.hotel_info = json.dumps(hotel_info)
        
        if ticket_doc or hotel_doc:
            registration.save(update_fields=['ticket_info', 'hotel_info'])

        print(f"DEBUG: About to call complete_travel_documents_step for registration {registration.id}. Doc count: {registration.travel_documents.count()}")
        
        result = complete_travel_documents_step(registration)
        
        print(f"DEBUG: complete_travel_documents_step result: {result}")
        
        if result and isinstance(result, dict) and result.get("error"):
            missing = result.get("missing", [])
            return api_response(
                success=False,
                message=f"Document uploaded but step not advanced. Please provide descriptions for all required documents: {', '.join(missing)}",
                errors={"missing_documents": missing},
                status_code=400
            )
        
        registration.refresh_from_db(fields=['current_step', 'updated_at'])
        print(f"DEBUG: After refresh, current_step: {registration.current_step}")

        return api_response(
            success=True,
            message="Travel document uploaded successfully",
            data=TravelDocumentSerializer(travel_doc).data,
            status_code=status.HTTP_201_CREATED
        )


# -----------------------------
# ADMIN: Upload Payment Details for User
# -----------------------------
class AdminUploadPaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def post(self, request, registration_id):
        if not self._is_admin(request.user):
            return api_response(success=False, message="Admin only", status_code=403)

        try:
            registration = Registration.objects.get(id=registration_id)
        except Registration.DoesNotExist:
            return api_response(success=False, message="Registration not found", status_code=404)

        serializer = PaymentDetailUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(success=False, message="Validation failed", errors=serializer.errors, status_code=400)

        payment_detail = PaymentDetail.objects.create(
            registration=registration,
            title=serializer.validated_data['title'],
            file=serializer.validated_data['file'],
            description=serializer.validated_data.get('description', ''),
            uploaded_by=request.user
        )

        result = complete_payment_details_step(registration)
        
        if result and isinstance(result, dict) and result.get("error"):
            missing = result.get("missing", [])
            return api_response(
                success=False,
                message=f"Payment detail uploaded but step not advanced. Please upload all required payment details: {', '.join(missing)}",
                errors={"missing_payment_details": missing},
                status_code=400
            )
        
        registration.refresh_from_db(fields=['current_step', 'updated_at'])

        return api_response(
            success=True,
            message="Payment detail uploaded successfully",
            data=PaymentDetailSerializer(payment_detail).data,
            status_code=status.HTTP_201_CREATED
        )


# -----------------------------
# USER: Upload Payment Proof
# -----------------------------
class UserUploadPaymentProofView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            registration = Registration.objects.exclude(status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]).get(user=request.user)
        except Registration.DoesNotExist:
            return api_response(success=False, message="No active registration found", status_code=404)

        title = request.data.get("title", "Payment Proof")
        file = request.FILES.get("file")
        description = request.data.get("description", "")

        if not file:
            return api_response(success=False, message="No file uploaded", status_code=400)

        payment_detail = PaymentDetail.objects.create(
            registration=registration,
            title=title,
            file=file,
            description=description,
            uploaded_by=request.user
        )

        complete_payment_details_step(registration)
        registration.refresh_from_db()
        
        # Notify admins
        try:
            user_name = f"{request.user.first_name or ''} {request.user.last_name or ''}".strip() or request.user.username or request.user.email
            admin_emails = list(User.objects.filter(can_approve_registrations=True, is_active=True, email__isnull=False).values_list('email', flat=True))
            if admin_emails:
                notify_admins_of_registration_event(admin_emails, 'payment_upload', user_name, registration.id)
        except Exception:
            pass

        return api_response(
            success=True,
            message="Payment proof uploaded successfully",
            data={"id": payment_detail.id},
            status_code=201
        )


# -----------------------------
# USER: View Their Travel Documents
# -----------------------------
class MyTravelDocumentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            registration = Registration.objects.exclude(status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]).get(user=request.user)
        except Registration.DoesNotExist:
            return api_response(success=False, message="No active registration found", status_code=404)

        travel_docs = registration.travel_documents.all()
        serializer = TravelDocumentSerializer(travel_docs, many=True)

        return api_response(
            success=True,
            message="Travel documents retrieved successfully",
            data=serializer.data
        )


# -----------------------------
# ADMIN: List all registrations
# -----------------------------
class AdminListRegistrationsView(APIView):
    permission_classes = [IsAuthenticated]

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def get(self, request):
        if not self._is_admin(request.user):
            return api_response(success=False, message="Admin only", status_code=403)

        registrations = Registration.objects.select_related(
            'user', 'current_step', 'package'
        ).prefetch_related(
            'completed_steps', 'travel_documents'
        ).order_by('-created_at')

        serializer = UserRegistrationSerializer(registrations, many=True)
        return api_response(success=True, data=serializer.data)


# -----------------------------
# ADMIN: Update journey details
# -----------------------------
class AdminUpdateJourneyDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def patch(self, request, registration_id):
        if not self._is_admin(request.user):
            return api_response(success=False, message="Admin only", status_code=403)

        try:
            registration = Registration.objects.get(id=registration_id)
        except Registration.DoesNotExist:
            return api_response(success=False, message="Registration not found", status_code=404)

        ticket_info = request.data.get("ticket_info")
        hotel_info = request.data.get("hotel_info")

        if ticket_info is not None:
            registration.ticket_info = ticket_info
        if hotel_info is not None:
            registration.hotel_info = hotel_info

        registration.save(update_fields=['ticket_info', 'hotel_info', 'updated_at'])

        return api_response(success=True, message="Journey details updated", data=UserRegistrationSerializer(registration).data)


# -----------------------------
# SUPPORT TICKET VIEWS
# -----------------------------
class MySupportTicketsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tickets = SupportTicket.objects.filter(user=request.user).prefetch_related('replies')
        serializer = SupportTicketSerializer(tickets, many=True)
        return api_response(success=True, data=serializer.data)


class CreateSupportTicketView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = SupportTicketCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(success=False, message="Validation failed", errors=serializer.errors, status_code=400)

        data = serializer.validated_data
        registration = None
        if reg_id := data.get('registration_id'):
            try:
                registration = Registration.objects.get(id=reg_id, user=request.user)
            except Registration.DoesNotExist:
                pass

        ticket = SupportTicket.objects.create(
            user=request.user,
            registration=registration,
            category=data['category'],
            subject=data['subject'],
            message=data['message']
        )

        # Send email notification to admin
        from core.services.email_service import send_support_ticket_email
        from django.conf import settings
        if settings.EMAIL_HOST_USER:
            send_support_ticket_email(
                admin_email=settings.EMAIL_HOST_USER,
                user_email=request.user.email or "",
                user_name=request.user.get_full_name() or request.user.username,
                subject=data['subject'],
                message=data['message'],
                category=data['category'],
                ticket_id=ticket.id
            )

        return api_response(
            success=True,
            message="Support ticket created successfully",
            data=SupportTicketSerializer(ticket).data,
            status_code=status.HTTP_201_CREATED
        )


class SupportTicketDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ticket_id):
        try:
            ticket = SupportTicket.objects.get(id=ticket_id, user=request.user)
        except SupportTicket.DoesNotExist:
            return api_response(success=False, message="Ticket not found", status_code=404)

        serializer = SupportTicketSerializer(ticket)
        return api_response(success=True, data=serializer.data)


class SupportTicketReplyView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, ticket_id):
        try:
            ticket = SupportTicket.objects.get(id=ticket_id, user=request.user)
        except SupportTicket.DoesNotExist:
            return api_response(success=False, message="Ticket not found", status_code=404)

        serializer = SupportTicketReplyCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(success=False, message="Validation failed", errors=serializer.errors, status_code=400)

        reply = SupportTicketReply.objects.create(
            ticket=ticket,
            user=request.user,
            message=serializer.validated_data['message']
        )
        ticket.status = 'in_progress' if ticket.status == 'open' else ticket.status
        ticket.save(update_fields=['status', 'updated_at'])

        return api_response(
            success=True,
            message="Reply added successfully",
            data=SupportTicketReplySerializer(reply).data,
            status_code=status.HTTP_201_CREATED
        )


# -----------------------------
# USER STATS & TRAVEL HISTORY
# -----------------------------
class UserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        all_registrations = Registration.objects.filter(user=user).order_by('-created_at')

        stats_record = UserDashboardStats.objects.filter(user=user).first()
        if not stats_record or (timezone.now() - stats_record.last_refresh).total_seconds() > 12 * 3600:
            stats_record = refresh_user_dashboard_stats(user.id)
        stats_payload = {
            'total_travels': stats_record.total_travels if stats_record else 0,
            'completed_travels': stats_record.completed_travels if stats_record else 0,
            'pending_travels': stats_record.in_progress_travels if stats_record else 0,
            'failed_travels': stats_record.failed_travels if stats_record else 0,
        }
        
        # Get current active registration (for sidebar)
        current_registration = all_registrations.filter(
            status__in=[RegistrationStatus.PENDING, RegistrationStatus.NOT_STARTED]
        ).first()
        
        # Get completed/failed registrations for travel history (limit 5)
        travel_history = []
        completed_registrations = all_registrations.filter(
            status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]
        ).order_by('-created_at')[:5]
        
        for reg in completed_registrations:
            # Calculate completed steps
            completed_count = reg.completed_steps.count()
            total_steps = RegistrationStep.objects.filter(is_active=True).count()
            
            travel_history.append({
                'id': reg.id,
                'package': reg.package.name if reg.package else None,
                'status': reg.status,
                'current_step': reg.current_step.title if reg.current_step else None,
                'created_at': reg.created_at.isoformat() if reg.created_at else None,
                'completed_at': reg.updated_at.isoformat() if reg.status == RegistrationStatus.COMPLETED else None,
                'steps_completed': completed_count,
                'total_steps': total_steps,
                'visa_status': reg.visa_status,
                'visa_status_notes': reg.visa_status_notes,
                'journey_presence_status': reg.journey_presence_status,
                'journey_presence_notes': reg.journey_presence_notes,
                'ticket_info': reg.ticket_info,
                'hotel_info': reg.hotel_info,
                'registration_date': reg.created_at.isoformat() if reg.created_at else None,
                'visa_issued_date': reg.updated_at.isoformat() if reg.visa_status == 'ready' else None,
                'flight_date': None,  # Would need to extract from ticket_info or add field
                'hotel_check_in': None,  # Would need to extract from hotel_info or add field
            })
        
        current_journey = None
        if current_registration:
            journey_presence = current_registration.journey_presence_status
            if journey_presence in ["arrived", "did_not_arrive"]:
                current_journey = None
            else:
                current_journey = {
                    'id': current_registration.id,
                    'package': current_registration.package.name if current_registration.package else None,
                    'status': current_registration.status,
                    'current_step': current_registration.current_step.title if current_registration.current_step else None,
                    'ticket_info': current_registration.ticket_info,
                    'hotel_info': current_registration.hotel_info,
                    'journey_presence_status': journey_presence,
                    'journey_presence_notes': current_registration.journey_presence_notes,
                }
        
        return api_response(
            success=True,
            data={
                'stats': stats_payload,
                'current_journey': current_journey,
                'travel_history': travel_history,
            }
        )


# -----------------------------
# REGISTRATION PROGRESS
# -----------------------------
class RegistrationProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Only get active registrations (not completed or failed)
        registration = Registration.objects.filter(
            user=user,
            status__in=['not_started', 'pending', 'in_progress']
        ).select_related('current_step', 'package').prefetch_related(
            'completed_steps'
        ).order_by('-created_at').first()
        
        if not registration:
            return api_response(
                success=True,
                data={'message': 'No active registration found'}
            )
        
        # Get all steps
        all_steps = list(RegistrationStep.objects.all().order_by('order').values('id', 'title', 'code'))
        completed_step_ids = set(registration.completed_steps.values_list('id', flat=True))
        
        # Build progress data
        progress_data = {
            'id': registration.id,
            'package': registration.package.name if registration.package else None,
            'status': registration.status,
            'current_step': registration.current_step.title if registration.current_step else None,
            'current_step_code': registration.current_step.code if registration.current_step else None,
            'all_steps': all_steps,
            'completed_step_ids': list(completed_step_ids),
            'steps_completed': len(completed_step_ids),
            'steps_remaining': len(all_steps) - len(completed_step_ids),
            'total_steps': len(all_steps),
            'created_at': registration.created_at.isoformat() if registration.created_at else None,
            'updated_at': registration.updated_at.isoformat() if registration.updated_at else None,
        }
        
        return api_response(
            success=True,
            data=progress_data
        )


# -----------------------------
# MANASIK GUIDANCE
# -----------------------------
class ManasikGuidanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        guidance = ManasikGuidance.objects.filter(is_active=True)
        
        if not guidance.exists():
            return api_response(
                success=True,
                data=self.get_default_guidance()
            )
        
        serializer = ManasikGuidanceSerializer(guidance, many=True)
        return api_response(success=True, data=serializer.data)

    def get_default_guidance(self):
        return [
            {
                "id": 1,
                "title": "What is Hajj?",
                "guidance_type": "general",
                "content": "Hajj is the annual Islamic pilgrimage to Mecca, Saudi Arabia. It is one of the Five Pillars of Islam and must be performed at least once in a lifetime by every adult Muslim who is physically and financially able.",
                "icon": "🏛️",
                "order": 1,
            },
            {
                "id": 2,
                "title": "Ihram",
                "guidance_type": "ihram",
                "content": "Upon entering the state of Ihram, pilgrims enter a spiritual sanctuary. Men wear two white sheets wrapped around the body, while women wear simple white dresses. During Ihram, certain actions are prohibited like cutting hair, trimming nails, and using perfume.",
                "icon": "🧵",
                "order": 2,
            },
            {
                "id": 3,
                "title": "Tawaf (Circumambulation)",
                "guidance_type": "tawaf",
                "content": "Pilgrims walk counter-clockwise seven times around the Ka'bah, the cubic building in Mecca. This symbolizes the devotion to Allah and encompasses all of humanity in a single act of worship.",
                "icon": "☪️",
                "order": 3,
            },
            {
                "id": 4,
                "title": "Sa'i (Walking)",
                "guidance_type": "tawaf",
                "content": "Pilgrims walk seven times between the hills of Safa and Marwah, which commemorates Hagar's search for water in the desert. This ritual represents patience, perseverance, and trust in Allah.",
                "icon": "🚶",
                "order": 4,
            },
            {
                "id": 5,
                "title": "Arafat",
                "guidance_type": "general",
                "content": "On the ninth day of Hajj, pilgrims gather at Mount Arafat for the pinnacle of Hajj. This is where Prophet Muhammad delivered his farewell sermon. Standing at Arafat from midday to sunset is mandatory.",
                "icon": "🕋",
                "order": 5,
            },
            {
                "id": 6,
                "title": "Rami (Stoning the Devil)",
                "guidance_type": "general",
                "content": "Pilgrims throw pebbles at the Jamrat al-Aqabah, symbolic of stoning the devil. This commemorates Prophet Ibrahim's refusal to be tempted by Satan.",
                "icon": "🪨",
                "order": 6,
            },
            {
                "id": 7,
                "title": "Qurbani (Sacrifice)",
                "guidance_type": "general",
                "content": "After stoning the devil, pilgrims perform Qurbani (sacrifice), typically an animal like a sheep, goat, or cow. The meat is distributed to the poor.",
                "icon": "🐑",
                "order": 7,
            },
            {
                "id": 8,
                "title": "Tawaf al-Ifadah",
                "guidance_type": "tawaf",
                "content": "This final circumambulation of the Ka'bah must be performed before the end of Hajj. It is also known as the Tawaf of visitation.",
                "icon": "🏃",
                "order": 8,
            },
        ]


# -----------------------------
# EMERGENCY CONTACTS
# -----------------------------
class EmergencyContactsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = EmergencyContact.objects.filter(is_active=True)
        
        if not contacts.exists():
            return api_response(
                success=True,
                data=self.get_default_contacts()
            )
        
        serializer = EmergencyContactSerializer(contacts, many=True)
        return api_response(success=True, data=serializer.data)

    def get_default_contacts(self):
        return [
            {
                "id": 1,
                "name": "Customer Support",
                "contact_type": "phone",
                "value": "+234 800 123 4567",
                "description": "Available 24/7 for emergencies",
            },
            {
                "id": 2,
                "name": "WhatsApp Support",
                "contact_type": "whatsapp",
                "value": "+234 800 123 4567",
                "description": "Fast response via WhatsApp",
            },
            {
                "id": 3,
                "name": "Email Support",
                "contact_type": "email",
                "value": "support@assemblytravels.com",
                "description": "Non-urgent inquiries",
            },
            {
                "id": 4,
                "name": "Emergency Hotline",
                "contact_type": "phone",
                "value": "+234 800 999 9999",
                "description": "Life-threatening emergencies only",
            },
        ]


# -----------------------------
# TRAVEL HISTORY (Paginated)
# -----------------------------
class TravelHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        all_registrations = Registration.objects.filter(user=user).order_by('-created_at')
        total = all_registrations.count()
        
        start = (page - 1) * page_size
        end = start + page_size
        paginated_registrations = all_registrations[start:end]
        
        travel_history = []
        for reg in paginated_registrations:
            travel_history.append({
                'id': reg.id,
                'package': reg.package.name if reg.package else None,
                'status': reg.status,
                'current_step': reg.current_step.title if reg.current_step else None,
                'created_at': reg.created_at.isoformat() if reg.created_at else None,
                'completed_at': reg.updated_at.isoformat() if reg.status == 'completed' else None,
            })
        
        return api_response(
            success=True,
            data={
                'travel_history': travel_history,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': (total + page_size - 1) // page_size,
                }
            }
        )


# -----------------------------
# CANCEL REGISTRATION (Admin Only)
# -----------------------------
class CancelRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, registration_id):
        # Check if admin
        if not request.user.is_staff:
            return api_response(
                success=False,
                message="Only admins can cancel registrations",
                status_code=403
            )
        
        try:
            registration = Registration.objects.select_related('user').get(id=registration_id)
        except Registration.DoesNotExist:
            return api_response(
                success=False,
                message="Registration not found",
                status_code=404
            )
        
        if registration.status == 'completed':
            return api_response(
                success=False,
                message="Cannot cancel a completed registration",
                status_code=400
            )
        
        registration.status = 'failed'
        registration.save(update_fields=['status'])
        
        # Send cancellation email
        from core.services.email_service import send_registration_cancelled_email
        if registration.user.email:
            send_registration_cancelled_email(registration.user.email, registration.id)
        
        return api_response(
            success=True,
            message="Registration cancelled successfully",
            data={'id': registration.id, 'status': registration.status}
        )


# -----------------------------
# START NEW REGISTRATION (User)
# -----------------------------
class StartNewRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from packages.models import Package
        from .services import start_new_registration
        from .serializers import UserRegistrationSerializer

        package_id = request.data.get("package_id")
        if not package_id:
            return api_response(
                success=False,
                message="package_id is required",
                status_code=400
            )

        try:
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist:
            return api_response(
                success=False,
                message="Package not found",
                status_code=404
            )

        result = start_new_registration(request.user, package)

        if result is None:
            return api_response(
                success=False,
                message="Failed to start new registration",
                status_code=400
            )

        if isinstance(result, dict) and result.get("error"):
            if result["error"] == "active_exists":
                return api_response(
                    success=False,
                    message="You already have an active registration",
                    data={"registration_id": result["registration"].id},
                    status_code=400
                )
            if result["error"] == "no_steps":
                return api_response(
                    success=False,
                    message="No registration steps available",
                    status_code=400
                )

        serializer = UserRegistrationSerializer(result)
        
        # Notify admins
        try:
            user_name = f"{request.user.first_name or ''} {request.user.last_name or ''}".strip() or request.user.username or request.user.email
            admin_emails = list(User.objects.filter(can_approve_registrations=True, is_active=True, email__isnull=False).values_list('email', flat=True))
            if admin_emails:
                first_step = RegistrationStep.objects.filter(is_active=True).order_by('order').first()
                step_title = first_step.title if first_step else "Registration"
                notify_admins_of_registration_event(admin_emails, 'registration', user_name, result.id, step_title)
        except Exception:
            pass
        
        return api_response(
            success=True,
            message="New registration started successfully",
            data=serializer.data,
            status_code=201
        )


# -----------------------------
# ADMIN: SUPPORT TICKET MANAGEMENT
# -----------------------------
class AdminSupportTicketListView(APIView):
    permission_classes = [IsAuthenticated]

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def get(self, request):
        if not self._is_admin(request.user):
            return api_response(success=False, message="Admin only", status_code=403)

        status = request.query_params.get('status')
        assigned = request.query_params.get('assigned')

        tickets = SupportTicket.objects.select_related('user', 'assigned_to').prefetch_related('replies')

        if status:
            tickets = tickets.filter(status=status)
        if assigned == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
        elif assigned == 'me':
            tickets = tickets.filter(assigned_to=request.user)

        serializer = SupportTicketSerializer(tickets, many=True)
        return api_response(success=True, data=serializer.data)


class AdminAssignTicketView(APIView):
    permission_classes = [IsAuthenticated]

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def post(self, request, ticket_id):
        if not self._is_admin(request.user):
            return api_response(success=False, message="Admin only", status_code=403)

        action = request.data.get('action')

        try:
            ticket = SupportTicket.objects.get(id=ticket_id)
        except SupportTicket.DoesNotExist:
            return api_response(success=False, message="Ticket not found", status_code=404)

        if action == 'assign':
            ticket.assigned_to = request.user
            ticket.status = 'in_progress'
            ticket.save(update_fields=['assigned_to', 'status', 'updated_at'])
            return api_response(success=True, message="Ticket assigned to you", data=SupportTicketSerializer(ticket).data)

        elif action == 'unassign':
            if ticket.assigned_to != request.user and not request.user.is_superuser:
                return api_response(success=False, message="Cannot unassign another admin's ticket", status_code=403)
            ticket.assigned_to = None
            ticket.status = 'open'
            ticket.save(update_fields=['assigned_to', 'status', 'updated_at'])
            return api_response(success=True, message="Ticket unassigned", data=SupportTicketSerializer(ticket).data)

        return api_response(success=False, message="Invalid action", status_code=400)


class AdminCloseTicketView(APIView):
    permission_classes = [IsAuthenticated]

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def post(self, request, ticket_id):
        if not self._is_admin(request.user):
            return api_response(success=False, message="Admin only", status_code=403)

        response_text = request.data.get('response', '').strip()

        try:
            ticket = SupportTicket.objects.select_related('user').get(id=ticket_id)
        except SupportTicket.DoesNotExist:
            return api_response(success=False, message="Ticket not found", status_code=404)

        # Only assigned admin or superuser can close
        if ticket.assigned_to and ticket.assigned_to != request.user and not request.user.is_superuser:
            return api_response(success=False, message="Only the assigned admin can close this ticket", status_code=403)

        ticket.status = 'closed'
        ticket.resolved_response = response_text
        ticket.resolved_by = request.user
        ticket.save(update_fields=['status', 'resolved_response', 'resolved_by', 'updated_at'])

        # Send email to user
        from core.services.email_service import send_support_ticket_closed_email
        if ticket.user.email:
            send_support_ticket_closed_email(
                user_email=ticket.user.email,
                ticket_id=ticket.id,
                subject=ticket.subject,
                response=response_text
            )

        return api_response(success=True, message="Ticket closed", data=SupportTicketSerializer(ticket).data)
