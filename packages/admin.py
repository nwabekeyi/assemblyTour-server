from django.contrib import admin
from .models import Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "location",
        "category",
        "price_current",
        "duration_days",
        "duration_nights",
        "created_at",
    )
    search_fields = ("name", "location")
    readonly_fields = ("created_at", "updated_at")
