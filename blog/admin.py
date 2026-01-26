from django.contrib import admin
from django.utils import timezone
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author_name",
        "created_by",
        "is_published",
        "published_at",
        "read_time",  # ✅ show read_time in list view
    )

    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "author_name")
    list_filter = ("is_published",)

    readonly_fields = (
        "created_by",
        "views_count",
        "likes_count",
        "published_at",
    )

    fieldsets = (
        ("Content", {
            "fields": (
                "title",
                "slug",
                "excerpt",
                "content",
                "cover_image",
            )
        }),
        ("Author", {
            "fields": (
                "author_name",
                "author_image",
            )
        }),
        ("Publishing", {
            "fields": (
                "is_published",
                "published_at",
                "read_time",  # ✅ allow admin to set read_time
            )
        }),
        ("System", {
            "fields": (
                "created_by",
                "views_count",
                "likes_count",
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        # ✅ auto-set creator
        if not obj.created_by:
            obj.created_by = request.user

        # ✅ auto-publish date
        if obj.is_published and not obj.published_at:
            obj.published_at = timezone.now()

        super().save_model(request, obj, form, change)
