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

    # Fieldsets for viewing/editing a user
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': (
            'first_name', 'last_name', 'profile_picture', 'phone', 'date_of_birth',
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
            'fields': ('email', 'username', 'phone', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')
        }),
    )

    # Make fields read-only (except ones you want editable)
    readonly_fields = (
        'email', 'first_name', 'last_name', 'profile_picture', 'phone', 'date_of_birth', 'gender',
        'nationality', 'state_of_origin', 'passport_number', 'passport_expiry',
        'address', 'emergency_contact_name', 'emergency_contact_phone',
        'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
        'last_login', 'date_joined'
    )

    # Columns displayed in the user list
    list_display = (
        "email", "get_username_safe", "phone", "first_name", "last_name",
        "get_profile_picture_safe", "is_staff", "is_active"
    )

    # Add search fields
    search_fields = ("email", "username", "phone", "first_name", "last_name")
    ordering = ("email",)

    # -------------------------------
    # Helper methods to handle nulls
    # -------------------------------

    def get_username_safe(self, obj):
        """Return username or placeholder if null."""
        return obj.username or "(no username)"
    get_username_safe.short_description = "Username"

    def get_profile_picture_safe(self, obj):
        """Return profile picture URL or placeholder if null."""
        if obj.profile_picture:
            return obj.profile_picture
        return "(no profile picture)"
    get_profile_picture_safe.short_description = "Profile Picture"
