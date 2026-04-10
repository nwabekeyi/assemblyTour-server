from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

# Customize site titles
admin.site.site_header = "Assembly Tours Admin Dashboard"
admin.site.site_title = "Assembly Tours Admin Portal"
admin.site.index_title = "Welcome to Assembly Tours Administration"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    def get_profile_picture_link(self, obj):
        """Return profile picture as clickable button."""
        if obj.profile_picture:
            return format_html(
                '<a href="{}" target="_blank" class="button" style="background:#447e9b; color:white; padding:4px 8px;">Open Profile Picture</a>',
                obj.profile_picture
            )
        return "No profile picture"

    # Fieldsets for viewing/editing a user
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': (
            'first_name', 'last_name', 'phone', 'date_of_birth',
            'gender', 'nationality', 'state_of_origin', 'passport_number', 'passport_expiry',
            'address', 'emergency_contact_name', 'emergency_contact_phone'
        )}),
        ('Profile', {'fields': ('get_profile_picture_link',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'can_approve_registrations', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to show when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'phone', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'can_approve_registrations')
        }),
    )

    # Make fields read-only
    readonly_fields = (
        'email', 'first_name', 'last_name', 'profile_picture', 'phone', 'date_of_birth', 'gender',
        'nationality', 'state_of_origin', 'passport_number', 'passport_expiry',
        'address', 'emergency_contact_name', 'emergency_contact_phone',
        'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
        'last_login', 'date_joined', 'get_profile_picture_link'
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

    def get_profile_picture_safe(self, obj):
        """Return profile picture image or placeholder if null."""
        if obj.profile_picture:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:50%%;" /></a>',
                obj.profile_picture, obj.profile_picture
            )
        return "(no profile picture)"