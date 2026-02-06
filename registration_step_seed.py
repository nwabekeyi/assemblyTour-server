# registration_step_seed.py
import os
import sys
import django
from django.db import transaction, models

# -----------------------------
# SETUP DJANGO
# -----------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    django.setup()
except Exception as e:
    print("❌ Django setup failed:", e)
    sys.exit(1)

# -----------------------------
# IMPORT MODELS
# -----------------------------
from registrations.models import RegistrationStep, StepAction, StepDataScope

# -----------------------------
# HARD-CODED REGISTRATION STEPS
# -----------------------------
REGISTRATION_STEPS = [
    {
        "code": "account_setup",
        "title": "Change Username and Password",
        "description": (
            "Update your username and password to secure your account "
            "before proceeding with registration."
        ),
        "action_type": StepAction.FILL_FORM,
        "data_scope": StepDataScope.USER,
        "order": 1,
    },
    {
        "code": "registration_form",
        "title": "Complete Registrations",
        "description": (
            "Fill in your personal details including name, email, passport number, "
            "date of birth, address, and phone number."
        ),
        "action_type": StepAction.FILL_FORM,
        "data_scope": StepDataScope.REGISTRATION,
        "order": 2,
    },
    {
        "code": "document_upload",
        "title": "Upload All Documents",
        "description": (
            "Upload your international passport and yellow card for verification."
        ),
        "action_type": StepAction.UPLOAD,
        "data_scope": StepDataScope.DOCUMENTS,
        "order": 3,
    },
    {
        "code": "document_review",
        "title": "Passport Review",
        "description": (
            "Your documents are being reviewed. You will be notified if "
            "they are approved or rejected."
        ),
        "action_type": StepAction.APPROVAL,
        "data_scope": StepDataScope.DOCUMENTS,
        "order": 4,
    },
    {
        "code": "visa_status",
        "title": "Visa Status",
        "description": (
            "Track your visa status. Once ready, you will be able to download it."
        ),
        "action_type": StepAction.AUTO,
        "data_scope": StepDataScope.DOCUMENTS,
        "order": 5,
    },
    {
        "code": "journey_details",
        "title": "Journey Details",
        "description": (
            "View your journey information including ticket, hotel, "
            "and package benefits."
        ),
        "action_type": StepAction.AUTO,
        "data_scope": StepDataScope.FLIGHT,
        "order": 6,
    },
]

# -----------------------------
# UPSERT LOGIC
# -----------------------------
created = 0
updated = 0

for step in REGISTRATION_STEPS:
    with transaction.atomic():
        # Ensure no other step has the same order before upsert
        conflicting_step = RegistrationStep.objects.filter(order=step["order"]).exclude(code=step["code"]).first()
        if conflicting_step:
            max_order = RegistrationStep.objects.aggregate(max_order=models.Max("order"))["max_order"] or 0
            conflicting_step.order = max_order + 1
            conflicting_step.save(update_fields=["order"])
            print(f"⚠️ Shifted order of '{conflicting_step.code}' to {conflicting_step.order}")

        # Create or update the step
        obj, is_created = RegistrationStep.objects.update_or_create(
            code=step["code"],
            defaults={
                "title": step["title"],
                "description": step["description"],
                "action_type": step["action_type"],
                "data_scope": step["data_scope"],
                "order": step["order"],
                "is_active": True,
            }
        )

        if is_created:
            created += 1
            print(f"✅ Created step: {obj.order}. {obj.title}")
        else:
            updated += 1
            print(f"♻️ Updated step: {obj.order}. {obj.title}")

print("\n🎉 Registration steps upsert complete!")
print(f"➡️ Created: {created}")
print(f"➡️ Updated: {updated}")
