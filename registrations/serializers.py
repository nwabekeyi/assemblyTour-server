from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from .models import (
    HajjRegistration,
    RegistrationStep,
    RegistrationStepReview,
    TravelDocument,
    TravelDocumentType,
    SupportTicket,
    SupportTicketReply,
    ManasikGuidance,
    EmergencyContact,
)

User = get_user_model()


# -----------------------------
# STEP SERIALIZERS
# -----------------------------
class SimpleStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationStep
        fields = ['id', 'code', 'title', 'order', 'action_type', 'data_scope']


class RegistrationStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationStep
        fields = [
            'id',
            'code',
            'title',
            'order',
            'action_type',
            'data_scope',
        ]
        read_only_fields = fields


# -----------------------------
# USER REGISTRATION SERIALIZER
# -----------------------------
class UserHajjRegistrationSerializer(serializers.ModelSerializer):
    current_step = RegistrationStepSerializer(read_only=True)
    completed_steps = RegistrationStepSerializer(many=True, read_only=True)

    all_steps = serializers.SerializerMethodField()
    completed_step_codes = serializers.SerializerMethodField()

    # rejection reason for CURRENT step
    current_step_rejection_reason = serializers.SerializerMethodField()

    # travel documents from admin
    travel_documents = serializers.SerializerMethodField()

    # step reviews for tracking pending/approved/rejected status
    step_reviews = serializers.SerializerMethodField()

    # Current step status: "pending" (can fill), "awaiting_approval", "approved"
    current_step_status = serializers.SerializerMethodField()

    class Meta:
        model = HajjRegistration
        fields = [
            'id',
            'status',
            'visa_status',
            'visa_status_notes',
            'current_step',
            'current_step_status',
            'current_step_rejection_reason',
            'completed_steps',
            'all_steps',
            'completed_step_codes',
            'package',
            'passport_document',
            'yellow_card_document',
            'travel_documents',
            'step_reviews',
            'ticket_info',
            'hotel_info',
            'journey_presence_status',
            'journey_presence_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_completed_step_codes(self, obj):
        return [step.code for step in obj.completed_steps.all()]

    def get_all_steps(self, obj):
        steps = RegistrationStep.objects.filter(
            is_active=True
        ).order_by('order')
        return RegistrationStepSerializer(steps, many=True).data

    def get_current_step_rejection_reason(self, obj):
        if not obj.current_step:
            return None

        review = RegistrationStepReview.objects.filter(
            registration=obj,
            step=obj.current_step,
            status="rejected",
        ).first()

        return review.rejection_reason if review else None

    def get_travel_documents(self, obj):
        return TravelDocumentSerializer(obj.travel_documents.all(), many=True).data

    def get_step_reviews(self, obj):
        reviews = obj.step_reviews.all()
        return [
            {
                "step_code": r.step.code,
                "status": r.status,
                "rejection_reason": r.rejection_reason,
            }
            for r in reviews
        ]

    def get_current_step_status(self, obj):
        """Returns: 'pending' (can fill), 'awaiting_approval', 'approved'"""
        if not obj.current_step:
            return None
        
        step_code = obj.current_step.code
        
        # Check if already in completed steps
        if obj.completed_step_codes and step_code in obj.completed_step_codes:
            return "approved"
        
        # Check step_reviews for this step
        review = obj.step_reviews.filter(step=obj.current_step).first()
        
        if review:
            if review.status == "approved":
                return "approved"
            elif review.status == "pending":
                return "awaiting_approval"
            elif review.status == "rejected":
                return "rejected"
        
        # No review yet - user can fill
        return "pending"


# -----------------------------
# ACCOUNT SETUP
# -----------------------------
class AccountSetupSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        trim_whitespace=True
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate_username(self, value):
        user = self.context['request'].user
        value = value.strip()

        if (
            value
            and value != user.username
            and User.objects.filter(username=value)
            .exclude(pk=user.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                "This username is already taken."
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                "The two passwords do not match."
            )
        return attrs


# -----------------------------
# STEP 2: REGISTRATION FORM
# -----------------------------
class RegistrationFormSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(max_length=30, required=True)
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female')],
        required=True
    )
    profile_picture = serializers.ImageField(required=True)
    nationality = serializers.CharField(max_length=50, required=True)
    state_of_origin = serializers.CharField(max_length=50, required=False)
    passport_number = serializers.CharField(max_length=50, required=True)
    passport_expiry = serializers.DateField(required=True)
    address = serializers.CharField(required=True)
    emergency_contact_name = serializers.CharField(max_length=100, required=True)
    emergency_contact_phone = serializers.CharField(max_length=20, required=True)

    # ✅ AGE VALIDATION (18+)
    def validate_date_of_birth(self, value):
        today = date.today()

        age = today.year - value.year - (
            (today.month, today.day) < (value.month, value.day)
        )

        if age < 18:
            raise serializers.ValidationError(
                "You must be at least 18 years old to register for Hajj."
            )

        return value

    # ✅ PASSPORT EXPIRY (≥ 3 MONTHS)
    def validate_passport_expiry(self, value):
        today = date.today()
        minimum_valid_date = today + timedelta(days=90)

        if value <= minimum_valid_date:
            raise serializers.ValidationError(
                "Passport must be valid for at least 3 months from today."
            )

        return value


# -----------------------------
# STEP 3: DOCUMENT UPLOAD
# -----------------------------
class DocumentUploadSerializer(serializers.Serializer):
    passport = serializers.FileField(required=True)
    yellow_card = serializers.FileField(required=True)


# -----------------------------
# TRAVEL DOCUMENTS (Admin Uploaded)
# -----------------------------
class TravelDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TravelDocument
        fields = ['id', 'doc_type', 'title', 'file', 'description', 'uploaded_by_name', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by_name', 'uploaded_at']

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.username or obj.uploaded_by.email or obj.uploaded_by.phone
        return None


class TravelDocumentUploadSerializer(serializers.Serializer):
    doc_type = serializers.ChoiceField(choices=TravelDocumentType.choices)
    title = serializers.CharField(max_length=100)
    file = serializers.FileField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)


# -----------------------------
# SUPPORT TICKETS
# -----------------------------
class SupportTicketReplySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicketReply
        fields = ['id', 'user_name', 'message', 'is_internal', 'created_at']
        read_only_fields = ['id', 'user_name', 'created_at']

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.username or obj.user.email or obj.user.phone
        return None


class SupportTicketSerializer(serializers.ModelSerializer):
    replies = SupportTicketReplySerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'category', 'subject', 'message', 'status',
            'resolved_response', 'created_at', 'updated_at', 'replies'
        ]
        read_only_fields = ['id', 'status', 'resolved_response', 'created_at', 'updated_at']


class SupportTicketCreateSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=[
        ('registration', 'Registration'),
        ('payment', 'Payment'),
        ('documents', 'Documents'),
        ('travel', 'Travel Info'),
        ('visa', 'Visa'),
        ('other', 'Other'),
    ])
    registration_id = serializers.IntegerField(required=False, allow_null=True)
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()


class SupportTicketReplyCreateSerializer(serializers.Serializer):
    message = serializers.CharField()


# -----------------------------
# MANASIK GUIDANCE
# -----------------------------
class ManasikGuidanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManasikGuidance
        fields = ['id', 'title', 'guidance_type', 'content', 'icon', 'order', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']


# -----------------------------
# EMERGENCY CONTACTS
# -----------------------------
class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'name', 'contact_type', 'value', 'description', 'is_active', 'order']
        read_only_fields = ['id']
