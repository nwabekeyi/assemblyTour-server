import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    django.setup()
except Exception as e:
    print("Django setup failed:", e)
    sys.exit(1)

from django.contrib.auth import get_user_model
from registrations.models import HajjRegistration, RegistrationStep, RegistrationStatus
from packages.models import Package

User = get_user_model()

email = "amusaadeshola92@gmail.com"
username = "amusaadeshola2"
password = "amusaadeshola"
phone = "+2348000002"

package_id = input("Enter package ID (2 for Deluxe, 3 for Suite): ").strip()

if User.objects.filter(email=email).exists():
    print(f"User with email '{email}' already exists.")
    sys.exit(1)

try:
    package = Package.objects.get(id=package_id)
except Package.DoesNotExist:
    print(f"Package with ID '{package_id}' not found.")
    sys.exit(1)

user = User.objects.create_user(
    phone=phone,
    email=email,
    username=username,
    password=password,
    is_active=True,
    is_staff=False,
    is_superuser=False,
)

first_step = RegistrationStep.objects.filter(order=1).first()
if not first_step:
    print("No registration step found. Please run registration_step_seed.py first.")
    sys.exit(1)

registration = HajjRegistration.objects.create(
    user=user,
    package=package,
    current_step=first_step,
    status=RegistrationStatus.NOT_STARTED,
)

print(f"\n✅ User created successfully!")
print(f"   Email: {email}")
print(f"   Username: {username}")
print(f"   Password: {password}")
print(f"   Package: {package.name} ({package.category})")
print(f"   Registration ID: {registration.id}")