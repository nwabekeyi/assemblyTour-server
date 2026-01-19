from django.contrib import admin
from .models import Package

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "price_current", "duration_days", "duration_nights")
    search_fields = ("name", "location")
    readonly_fields = ("created_at", "updated_at")
