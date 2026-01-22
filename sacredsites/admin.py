from django.contrib import admin
from .models import SacredSite


@admin.register(SacredSite)
class SacredSiteAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    list_editable = ["is_active"]
    search_fields = ["name"]
