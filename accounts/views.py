import os
import random
import string
from datetime import timedelta
import requests
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AuthSerializer, UserProfileSerializer, RequestPasswordResetSerializer, VerifyPasswordResetOTPSerializer, ResetPasswordSerializer
from .validators import AuthData
from core.utils.api_response import api_response
from core.utils.validators import validate_with_pydantic
from packages.models import Package
from django.db import transaction
from registrations.models import Registration, RegistrationStep, RegistrationStatus
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import PasswordResetToken
import logging
from core.services.email_service import send_password_reset_otp_email


User = get_user_model()


@method_decorator(ratelimit(key='ip', rate='10/m', block=True), name='dispatch')
class AuthView(generics.GenericAPIView):
    serializer_class = AuthSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        # 1️⃣ Validate input with Pydantic
        validated_data = validate_with_pydantic(AuthData, request.data)

        # 2️⃣ Validate with DRF serializer
        serializer = self.get_serializer(data=validated_data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']

        if action == 'register':
            return self._register(serializer.validated_data)
        elif action == 'login':
            return self._login(serializer.validated_data)
        elif action == 'refresh':
            return self._refresh_token(serializer.validated_data)

    # -----------------------
    # Registration logic
    # -----------------------
    def _register(self, data):
        # Package
        package_id = data.get("package_id")
        package = Package.objects.get(id=package_id)

        # 2b️⃣ Check for existing active registration using email
        user_email = data.get('email', '').lower()
        existing = Registration.objects.filter(
            user__email=user_email
        ).exclude(
            status__in=[RegistrationStatus.COMPLETED, RegistrationStatus.FAILED]
        ).first()
        
        if existing:
            return api_response(
                success=False,
                message="You already have an active registration. Please complete or cancel it before starting a new one.",
                data=None,
                errors={"existing_registration": "Active registration exists"},
                status_code=400,
            )

        # 2c️⃣ Check if email already exists
        if User.objects.filter(email=user_email).exists():
            return api_response(
                success=False,
                message="An account with this email already exists.",
                data=None,
                errors={"email": "A user with this email already exists."},
                status_code=400,
            )

        # 3️⃣ Transactional creation
        with transaction.atomic():
            username = "user" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

            user = User.objects.create_user(
                phone=None,
                email=user_email,
                username=username,
                password=temp_password
            )

            first_step = RegistrationStep.objects.get(order=1)
            Registration.objects.create(user=user, current_step=first_step, package=package)

            refresh = RefreshToken.for_user(user)

        # 4️⃣ Send login credentials via email (async, non-blocking)
        import threading
        import logging
        from core.services.email_service import send_login_credentials_email
        def send_email_async():
            try:
                send_login_credentials_email(
                    user_email=user_email,
                    username=username,
                    temp_password=temp_password,
                    package_name=package.name
                )
            except Exception as e:
                logging.error(f"Failed to send login credentials to {user_email}: {e}")
        threading.Thread(target=send_email_async, daemon=True).start()

        # 5️⃣ Response
        return api_response(
            success=True,
            message="User registered successfully",
            data={
                "user": {"id": user.id, "username": user.username, "email": user.email, "package": {"id": package.id, "name": package.name}},
                "tokens": {"refresh": str(refresh), "access": str(refresh.access_token)},
            },
            errors=None,
            status_code=201,
        )

    # -----------------------
    # Login logic using username + password
    # -----------------------
    def _login(self, data):
        try:
            user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            return api_response(
                success=False,
                message="Invalid login credentials",
                data=None,
                errors={"detail": "Invalid username or password"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(data['password']):
            return api_response(
                success=False,
                message="Invalid login credentials",
                data=None,
                errors={"detail": "Invalid username or password"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return api_response(
            success=True,
            message="Login successful",
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "phone": user.phone,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            errors=None,
            status_code=status.HTTP_200_OK,
        )

class RefreshTokenView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return api_response(
                success=False,
                message="Refresh token is required",
                data=None,
                errors={"refresh": "This field is required"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
        except Exception:
            return api_response(
                success=False,
                message="Invalid refresh token",
                data=None,
                errors={"detail": "Invalid refresh token"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        return api_response(
            success=True,
            message="Access token refreshed successfully",
            data={
                "access": str(refresh.access_token),
            },
            errors=None,
            status_code=status.HTTP_200_OK,
        )

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Return the currently authenticated user
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return api_response(
            data=serializer.data,
            message="User profile fetched successfully"
        )


# ───────────────────────────────
# Password Reset Views
# ───────────────────────────────
@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class RequestPasswordResetView(generics.GenericAPIView):
    """
    Step 1: Request password reset.
    Generates a 6-digit OTP and sends it to the user's email.
    """
    serializer_class = RequestPasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))

        # Create or update token
        expires_at = timezone.now() + timedelta(minutes=10)
        token_obj = PasswordResetToken.objects.create(
            user=user,
            token=otp,
            expires_at=expires_at
        )

        # Send OTP via email
        try:
            send_password_reset_otp_email(user.email, otp)
        except Exception as e:
            return api_response(
                success=False,
                message="Failed to send OTP. Please try again.",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return api_response(
            success=True,
            message="OTP sent to your email address.",
            data={"email": email},  # Don't send token back in response
            status_code=status.HTTP_200_OK
        )


@method_decorator(ratelimit(key='ip', rate='10/m', block=True), name='dispatch')
class VerifyPasswordResetOTPView(generics.GenericAPIView):
    """
    Step 2: Verify the OTP sent to email.
    """
    serializer_class = VerifyPasswordResetOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        reset_token = serializer.validated_data['reset_token']

        # Token is already validated in serializer
        # Return success
        return api_response(
            success=True,
            message="OTP verified successfully. You can now reset your password.",
            data={"email": email, "token": reset_token.token},
            status_code=status.HTTP_200_OK
        )


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class ResetPasswordView(generics.GenericAPIView):
    """
    Step 3: Reset password after OTP verification.
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save(attrs=serializer.validated_data)

        # Optionally log the user in after password reset
        # Generate new tokens
        refresh = RefreshToken.for_user(user)

        return api_response(
            success=True,
            message="Password reset successfully. You can now log in with your new password.",
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            },
            status_code=status.HTTP_200_OK
        )
