from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=20, unique=True)
    registration_id = models.CharField(max_length=30, unique=True)

    # FIX reverse accessor clashes
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
