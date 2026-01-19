from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid


# ---------------------------
# Custom User Manager
# ---------------------------
class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, phone, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not phone:
            raise ValueError("Phone is required")

        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, phone, password, **extra_fields)


# ---------------------------
# Custom User Model
# ---------------------------
class User(AbstractUser):
    username = None

    # Required fields
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    registration_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Optional personal info for Hajj registration
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female')],
        null=True,
        blank=True
    )
    nationality = models.CharField(max_length=50, null=True, blank=True)
    state_of_origin = models.CharField(max_length=50, null=True, blank=True)
    passport_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, null=True, blank=True)

    # Django fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Avoid reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='accounts_users',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='accounts_users_permissions',
        blank=True,
    )

    # Use email as login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    objects = UserManager()

    def __str__(self):
        return self.email
