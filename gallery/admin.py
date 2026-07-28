from django.contrib import admin
from .models import Gallery


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ["title", "media_type", "is_active", "display_order", "created_at", "created_by"]
    list_filter = ["media_type", "is_active", "created_at"]
    list_editable = ["is_active", "display_order"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_by", "created_at", "updated_at"]
    search_fields = ["title", "description"]

    fieldsets = (
        ("Media", {
            "fields": (
                "title",
                "slug",
                "media_type",
                "url",
                "thumbnail",
                "media",
            )
        }),
        ("Description", {
            "fields": (
                "description",
            )
        }),
        ("Display settings", {
            "fields": (
                "is_active",
                "display_order",
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

    class Media:
        js = ("admin/js/gallery_admin.js",)

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
