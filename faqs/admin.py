from django.contrib import admin
from .models import FAQ

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")
    readonly_fields = ("created_at", "updated_at")
