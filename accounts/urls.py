from django.urls import path
from .views import AuthView, UserProfileView, RefreshTokenView

urlpatterns = [
    path("auth/", AuthView.as_view(), name="auth"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("user/profile/", UserProfileView.as_view(), name="user-profile"),
]
