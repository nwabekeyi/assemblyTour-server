from django.contrib import admin
from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at']
    search_fields = ['author_name', 'content']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = (
        ("Content", {
            "fields": (
                "author_name",
                "author_image",
                "content",
            )
        }),
        ("Settings", {
            "fields": (
                "is_active",
            )
        }),
        ("System", {
            "fields": (
                "created_by",
                "created_at",
                "updated_at",
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)