from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Customize site titles
admin.site.site_header = "Assembly Tours Admin Dashboard"
admin.site.site_title = "Assembly Tours Admin Portal"
admin.site.index_title = "Welcome to Assembly Tours Administration"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    # Only allow password to be editable, everything else read-only
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': (
            'first_name', 'last_name', 'phone', 'date_of_birth',
            'gender', 'nationality', 'state_of_origin', 'passport_number', 'passport_expiry',
            'address', 'emergency_contact_name', 'emergency_contact_phone'
        )}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to show when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')
        }),
    )

    # Make all fields read-only except password
    readonly_fields = (
        'email', 'first_name', 'last_name', 'phone', 'date_of_birth', 'gender',
        'nationality', 'state_of_origin', 'passport_number', 'passport_expiry',
        'address', 'emergency_contact_name', 'emergency_contact_phone',
        'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
        'last_login', 'date_joined'
    )

    # Columns displayed in the user list
    list_display = ("email", "phone", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("email", "phone", "first_name", "last_name")
    ordering = ("email",)
