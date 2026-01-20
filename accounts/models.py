from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import cuid

# ---------------------------
# CUID generator
# ---------------------------
def generate_cuid():
    return cuid.cuid()


# ---------------------------
# Custom User Manager
# ---------------------------
class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone, password=None, email=None, username=None, **extra_fields):
        if not phone:
            raise ValueError("Phone is required")

        if email:
            email = self.normalize_email(email)

        user = self.model(
            phone=phone,
            email=email,
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, email=None, username=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not email:
            raise ValueError("Superuser must have an email")

        return self.create_user(
            phone=phone,
            email=email,
            password=password,
            username=username,
            **extra_fields
        )



# ---------------------------
# Custom User Model (CUID)
# ---------------------------
class User(AbstractUser):
    # 🔑 CUID primary key
    id = models.CharField(
        max_length=25,
        primary_key=True,
        default=generate_cuid,
        editable=False
    )

    # Make username optional
    username = models.CharField(max_length=150, blank=True, null=True, unique=True)

    # Required fields
    phone = models.CharField(max_length=20, unique=True)

    # Optional personal info
    first_name = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True
    )
    last_name = models.CharField(max_length=30, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female')],
        null=True,
        blank=True
    )
    profile_picture = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL to the user's profile picture"
    )
    nationality = models.CharField(max_length=50, null=True, blank=True)
    state_of_origin = models.CharField(max_length=50, null=True, blank=True)
    passport_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, null=True, blank=True)

    # Django flags
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

    # Auth config
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']  # username is optional now

    objects = UserManager()

    def __str__(self):
        return self.email
