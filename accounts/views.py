import os
import random
import string
import requests
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AuthSerializer, UserProfileSerializer
from .validators import AuthData
from core.utils.api_response import api_response
from core.utils.validators import validate_with_pydantic
from packages.models import Package
from django.db import transaction
from registrations.models import HajjRegistration, RegistrationStep, RegistrationStatus


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
        # 1️⃣ Turnstile verification
        turnstile_secret = os.getenv("CLOUDFLARE_SECRET_KEY")
        token = data.get("turnstileToken")
        if not token:
            return api_response(False, "Turnstile token is missing", None, {"detail": "No token"}, 400)

        resp = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": turnstile_secret, "response": token},
            timeout=5
        )
        result = resp.json()
        if not result.get("success"):
            return api_response(False, "Turnstile verification failed", None, {"detail": result.get("error-codes", "Unknown")}, 400)

        # 2️⃣ Package
        package_id = data.get("package_id")
        package = Package.objects.get(id=package_id)

        # 2b️⃣ Check for existing active registration using email
        user_email = data.get('email', '').lower()
        existing = HajjRegistration.objects.filter(
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
                phone="",
                email=user_email,
                username=username,
                password=temp_password
            )

            first_step = RegistrationStep.objects.get(order=1)
            HajjRegistration.objects.create(user=user, current_step=first_step, package=package)

            refresh = RefreshToken.for_user(user)

        # 4️⃣ Send login credentials via email
        from core.services.email_service import send_login_credentials_email
        send_login_credentials_email(
            user_email=user_email,
            username=username,
            temp_password=temp_password,
            package_name=package.name
        )

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
