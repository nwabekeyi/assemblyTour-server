# seed_first_registration_step.py
import os
import django
import sys

# Point to your Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    django.setup()
except Exception as e:
    print("Django setup failed:", e)
    sys.exit(1)

from hajj.models import RegistrationStep, StepAction, StepDataScope

# Step details
step_code = "change_credentials"
step_title = "Change Username and Password"
step_description = (
    "As your first step, update your username and password to secure your account."
)
step_order = 1  # First step

# Check if the step already exists
if RegistrationStep.objects.filter(code=step_code).exists():
    print(f"Step '{step_title}' already exists.")
    sys.exit(0)

# Create the first registration step
first_step = RegistrationStep.objects.create(
    code=step_code,
    title=step_title,
    description=step_description,
    action_type=StepAction.FILL_FORM,
    data_scope=StepDataScope.USER,
    order=step_order,
    is_active=True,
)

print(f"First registration step created successfully: '{first_step}'")
