from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PasswordResetToken

User = get_user_model()


# ───────────────────────────────
# Authentication Serializer
# ───────────────────────────────
class AuthSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['register', 'login', 'refresh'],
        help_text="Action to perform: register, login, or refresh"
    )

    # Fields
    username = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False)
    refresh = serializers.CharField(write_only=True, required=False)
    package_id = serializers.IntegerField(write_only=True, required=False)

    def validate(self, attrs):
        action = attrs.get('action')

        if action == 'register':
            required_fields = ['email']  # require email for registration
        elif action == 'login':
            required_fields = ['username', 'password']
        elif action == 'refresh':
            required_fields = ['refresh']
        else:
            required_fields = []

        missing = [f for f in required_fields if not attrs.get(f)]
        if missing:
            raise serializers.ValidationError({
                field: f"This field is required for {action}"
                for field in missing
            })

        return attrs


# ───────────────────────────────
# User Profile Serializer
# ───────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.URLField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "profile_picture",
            "nationality",
            "state_of_origin",
            "passport_number",
            "passport_expiry",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
        ]


# ───────────────────────────────
# Password Reset Serializers
# ───────────────────────────────
class RequestPasswordResetSerializer(serializers.Serializer):
    """Serializer for requesting password reset (sends OTP)."""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Ensure user with this email exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email address.")
        return value


class VerifyPasswordResetOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP."""
    email = serializers.EmailField(required=True)
    token = serializers.CharField(max_length=6, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        token = attrs.get('token')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email address."})

        # Check if token exists and is valid
        reset_token = PasswordResetToken.objects.filter(
            user=user,
            token=token,
            is_used=False
        ).first()

        if not reset_token:
            raise serializers.ValidationError({"token": "Invalid or already used token."})

        if not reset_token.is_valid():
            raise serializers.ValidationError({"token": "Token has expired. Please request a new one."})

        attrs['user'] = user
        attrs['reset_token'] = reset_token
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password after OTP verification."""
    email = serializers.EmailField(required=True)
    token = serializers.CharField(max_length=6, required=True)
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        token = attrs.get('token')
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email address."})

        # Verify token
        reset_token = PasswordResetToken.objects.filter(
            user=user,
            token=token,
            is_used=False
        ).first()

        if not reset_token:
            raise serializers.ValidationError({"token": "Invalid or already used token."})

        if not reset_token.is_valid():
            raise serializers.ValidationError({"token": "Token has expired. Please request a new one."})

        attrs['user'] = user
        attrs['reset_token'] = reset_token
        return attrs

    def save(self, attrs):
        """Update user password and mark token as used."""
        user = attrs['user']
        reset_token = attrs['reset_token']
        password = attrs['password']

        user.set_password(password)
        user.save()

        # Mark token as used
        reset_token.is_used = True
        reset_token.save()

        return user

