# create_test_user.py
import os
import django
import sys

# Point to your settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    django.setup()
except Exception as e:
    print("Django setup failed:", e)
    sys.exit(1)

from django.contrib.auth import get_user_model

User = get_user_model()

# Test user credentials
username = "testuser"
password = "testpass123"
email = "testuser@example.com"
phone = "+2348000000001"

# Detect login field dynamically (email / phone / etc.)
USERNAME_FIELD = User.USERNAME_FIELD

# Build lookup safely
lookup = {USERNAME_FIELD: email}

# Prevent duplicates
if User.objects.filter(**lookup).exists():
    print(f"Test user with {USERNAME_FIELD}='{email}' already exists.")
    sys.exit(0)

# Required fields for your custom user model
extra_fields = {
    "username": username,
    "phone": phone,
    "is_active": True,
    "is_staff": False,
    "is_superuser": False,
}

# Create user safely
user = User.objects.create_user(
    **lookup,
    password=password,
    **extra_fields
)

print(
    f"Test user created successfully "
    f"({USERNAME_FIELD}='{email}', username='{username}')"
)
