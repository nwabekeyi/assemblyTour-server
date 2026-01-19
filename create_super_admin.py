# create_super_admin.py
import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    django.setup()
except Exception as e:
    print("Django setup failed:", e)
    sys.exit(1)

from django.contrib.auth import get_user_model

User = get_user_model()

# Detect the actual login field (email, phone, etc.)
USERNAME_FIELD = User.USERNAME_FIELD

# Read env variables
identifier = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

if not identifier or not password:
    print("Superuser env vars not set. Skipping superuser creation.")
    sys.exit(0)

lookup = {USERNAME_FIELD: identifier}

if User.objects.filter(**lookup).exists():
    print(f"Superuser with {USERNAME_FIELD}='{identifier}' already exists.")
    sys.exit(0)

# Hardcode a phone number for superuser
phone = os.environ.get("DJANGO_SUPERUSER_PHONE", "+2348000000000")

# Build required fields dynamically
extra_fields = {
    "is_staff": True,
    "is_superuser": True,
    "phone": phone,  # REQUIRED by custom user model
}

# Create superuser safely
user = User.objects.create_user(
    **lookup,
    password=password,
    **extra_fields
)

print(f"Superuser '{identifier}' created successfully with phone {phone}.")
