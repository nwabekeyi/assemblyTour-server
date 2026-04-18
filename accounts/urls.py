from django.urls import path
from .views import AuthView, UserProfileView, RefreshTokenView, RequestPasswordResetView, VerifyPasswordResetOTPView, ResetPasswordView

urlpatterns = [
    path("auth/", AuthView.as_view(), name="auth"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("user/profile/", UserProfileView.as_view(), name="user-profile"),
    # Password reset endpoints
    path("auth/request-password-reset/", RequestPasswordResetView.as_view(), name="request-password-reset"),
    path("auth/verify-password-reset-otp/", VerifyPasswordResetOTPView.as_view(), name="verify-password-reset-otp"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]
