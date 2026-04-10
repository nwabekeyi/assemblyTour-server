from django.contrib import admin
from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at']
    search_fields = ['author_name', 'content']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']