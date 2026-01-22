from django.contrib import admin
from .models import BlogPost, BlogComment, BlogLike

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published")  # don't show author, admin knows they posted it
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title",)
    list_filter = ("is_published",)
    readonly_fields = ("views_count", "likes_count", "published_at")  # read-only
    exclude = ("author",)  # hide author from form

    def save_model(self, request, obj, form, change):
        # Auto-set the author to the logged-in user
        if not obj.author:
            obj.author = request.user
        # Auto-set published_at if blog is being published
        if obj.is_published and not obj.published_at:
            from django.utils import timezone
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)


# @admin.register(BlogComment)
# class BlogCommentAdmin(admin.ModelAdmin):
#     list_display = ("post", "user", "created_at")
#     readonly_fields = ("created_at",)


# @admin.register(BlogLike)
# class BlogLikeAdmin(admin.ModelAdmin):
#     list_display = ("post", "user", "created_at")
#     readonly_fields = ("created_at",)
