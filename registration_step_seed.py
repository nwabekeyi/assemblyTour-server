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
        "code": "payment_details",
        "title": "Payment Details",
        "description": (
            "Upload your payment proof (bank transfer slip, receipt, etc.) "
            "so our finance team can verify and process your payment."
        ),
        "action_type": StepAction.UPLOAD,
        "data_scope": StepDataScope.PAYMENT,
        "order": 3,
    },
    {
        "code": "payment_review",
        "title": "Payment Review",
        "description": (
            "Your payment is being reviewed by our finance team. "
            "You will be notified once it's approved or if additional information is needed."
        ),
        "action_type": StepAction.APPROVAL,
        "data_scope": StepDataScope.PAYMENT,
        "order": 4,
    },
    {
        "code": "document_upload",
        "title": "Upload All Documents",
        "description": (
            "Upload your international passport and yellow card for verification."
        ),
        "action_type": StepAction.UPLOAD,
        "data_scope": StepDataScope.DOCUMENTS,
        "order": 5,
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
        "order": 7,
    },
    {
        "code": "visa_status",
        "title": "Visa Status",
        "description": (
            "Track your visa status. Once ready, you will be able to download it."
        ),
        "action_type": StepAction.AUTO,
        "data_scope": StepDataScope.DOCUMENTS,
        "order": 8,
    },
    {
        "code": "travel_documents",
        "title": "Travel Documents",
        "description": (
            "Upload flight tickets, visas, and hotel vouchers once they are issued."
        ),
        "action_type": StepAction.UPLOAD,
        "data_scope": StepDataScope.DOCUMENTS,
        "order": 9,
    },
    {
        "code": "arrival_status",
        "title": "Arrival Status",
        "description": (
            "Track traveler presence from the awaiting travel state "
            "through arrival or incident reporting."
        ),
        "action_type": StepAction.AUTO,
        "data_scope": StepDataScope.FLIGHT,
        "order": 10,
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

# -----------------------------
# CLEANUP: Remove steps not in our defined list
# -----------------------------
from registrations.models import HajjRegistration

known_codes = {step["code"] for step in REGISTRATION_STEPS}
deleted = 0

# Get the fallback step from our list
fallback_step = RegistrationStep.objects.filter(code__in=known_codes).order_by('-order').first()

for step in RegistrationStep.objects.all():
    if step.code not in known_codes:
        if fallback_step:
            updated = HajjRegistration.objects.filter(current_step=step).update(current_step=fallback_step)
            if updated:
                print(f"⚠️ Updated {updated} registrations to '{fallback_step.code}'")
        print(f"🗑️Removing unknown step: {step.code} (order {step.order})")
        step.delete()
        deleted += 1

print("\n🎉 Registration steps upsert complete!")
print(f"➡️ Created: {created}")
print(f"➡️ Updated: {updated}")
print(f"➡️ Deleted: {deleted}")
