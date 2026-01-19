from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.permissions import AllowAny
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
        # 1️⃣ Validate with Pydantic
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
        import random
        import string

        temp_password = ''.join(
            random.choices(string.ascii_letters + string.digits, k=10)
        )

        user = User(
            username=data['username'],
            email=data['email'],
            phone=data['phone'],
        )
        user.set_password(temp_password)
        user.save()

        refresh = RefreshToken.for_user(user)

        return api_response(
            success=True,
            message="User registered successfully",
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "registration_id": user.registration_id,
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
    # Login logic using email + password
    # -----------------------
    def _login(self, data):
        # Find user by email
        user = User.objects.get(email=data['email'])

        # Check password manually
        if not user.check_password(data['password']):
            return api_response(
                success=False,
                message="Invalid login credentials",
                data=None,
                errors={"detail": "Invalid email or password"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Everything is fine, create JWT tokens
        refresh = RefreshToken.for_user(user)

        return api_response(
            success=True,
            message="Login successful",
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "registration_id": user.registration_id,
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
        refresh_token = data['refresh']
        refresh = RefreshToken(refresh_token)

        return api_response(
            success=True,
            message="Access token refreshed successfully",
            data={
                "access": str(refresh.access_token),
            },
            errors=None,
            status_code=status.HTTP_200_OK,
        )

