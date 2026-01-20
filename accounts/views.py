import os
import random
import string
import requests
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AuthSerializer
from .validators import AuthData
from core.utils.api_response import api_response
from core.utils.validators import validate_with_pydantic

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
        # 1️⃣ Get Turnstile secret from environment
        turnstile_secret = os.getenv("CLOUDFLARE_SECRET_KEY")
        token = data.get("turnstileToken")

        if not token:
            return api_response(
                success=False,
                message="Turnstile token is missing",
                data=None,
                errors={"detail": "No token provided"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 2️⃣ Verify Turnstile token
        try:
            resp = requests.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": turnstile_secret,
                    "response": token
                },
                timeout=5
            )
            result = resp.json()
        except requests.RequestException as e:
            return api_response(
                success=False,
                message="Turnstile verification failed",
                data=None,
                errors={"detail": str(e)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not result.get("success"):
            return api_response(
                success=False,
                message="Turnstile verification failed",
                data=None,
                errors={"detail": result.get("error-codes", "Unknown error")},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 3️⃣ Generate username and temporary password
        username = "user" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # 4️⃣ Create user with phone only
        user = User.objects.create_user(
            phone=data['phone'],
            username=username,
            password=temp_password
        )

        # 5️⃣ Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return api_response(
            success=True,
            message="User registered successfully",
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "phone": user.phone,
                },
                "temp_password": temp_password,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            errors=None,
            status_code=status.HTTP_201_CREATED,
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

    # -----------------------
    # Refresh token logic
    # -----------------------
    def _refresh_token(self, data):
        try:
            refresh = RefreshToken(data['refresh'])
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
            data={"access": str(refresh.access_token)},
            errors=None,
            status_code=status.HTTP_200_OK,
        )
