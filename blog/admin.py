from django.contrib import admin
from .models import BlogPost, BlogComment


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "is_published", "views_count", "likes_count")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title",)
    list_filter = ("is_published",)


# @admin.register(BlogComment)
# class BlogCommentAdmin(admin.ModelAdmin):
#     list_display = ("post", "user", "created_at")
