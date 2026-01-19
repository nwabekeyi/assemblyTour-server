from django.urls import path
from .views import UserRegistrationStepsView

urlpatterns = [
    path("registration/steps/", UserRegistrationStepsView.as_view(), name="user-registration-steps"),
]
