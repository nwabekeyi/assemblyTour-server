# urls.py
from django.urls import path
from .views import (
    MyHajjRegistrationView,
    AccountSetupView,
    RegistrationFormView,
    DocumentUploadView,
)

urlpatterns = [
    # ─── Current / existing endpoint ─────────────────────────────────────
    path('registration/my/', MyHajjRegistrationView.as_view(), name='my-hajj-registration'),

    # ─── Step 1 – Change username & password ─────────────────────────────
    path('hajj/step/account-setup/', AccountSetupView.as_view(), name='hajj-account-setup'),

    # ─── Step 2 – Fill personal details (user model) ─────────────────────
    path('hajj/step/registration-form/', RegistrationFormView.as_view(), name='hajj-registration-form'),

    # ─── Step 3 – Upload passport & yellow card ──────────────────────────
    path('hajj/step/document-upload/', DocumentUploadView.as_view(), name='hajj-document-upload'),
]