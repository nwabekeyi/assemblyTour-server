from django.contrib import admin
from .models import BankAccount, PaymentInstruction


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("bank_name", "account_name", "account_number", "account_type", "is_active", "is_primary")
    list_filter = ("is_active", "account_type")
    search_fields = ("bank_name", "account_name", "account_number")
    list_editable = ("is_active", "is_primary")
    ordering = ["-is_primary", "-is_active", "bank_name"]

    fieldsets = (
        (None, {
            "fields": ("bank_name", "account_name", "account_number", "account_type")
        }),
        ("Status", {
            "fields": ("is_active", "is_primary")
        }),
        ("Additional Info", {
            "fields": ("notes", "created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ("created_by", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PaymentInstruction)
class PaymentInstructionAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active")
    list_filter = ("is_active",)
    list_editable = ("is_active", "order")
    search_fields = ("title", "content")
    ordering = ["order", "-is_active"]