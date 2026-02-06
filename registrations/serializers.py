from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from .models import (
    HajjRegistration,
    RegistrationStep,
    RegistrationStepReview,
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

    class Meta:
        model = HajjRegistration
        fields = [
            'id',
            'status',
            'current_step',
            'current_step_rejection_reason',
            'completed_steps',
            'all_steps',
            'completed_step_codes',
            'package',
            'passport_document',
            'yellow_card_document',
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

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                "The two passwords do not match."
            )
        return data


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
