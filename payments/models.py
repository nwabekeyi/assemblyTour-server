from django.db import models
from django.conf import settings


class BankAccount(models.Model):
    """Bank accounts for receiving payments - managed by admin."""
    bank_name = models.CharField(max_length=100, help_text="e.g., First Bank, Zenith Bank")
    account_name = models.CharField(max_length=150, help_text="Account holder name")
    account_number = models.CharField(max_length=20, help_text="Account number")
    account_type = models.CharField(
        max_length=20,
        choices=[
            ("savings", "Savings"),
            ("current", "Current"),
        ],
        default="savings"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this account is currently displayed to users")
    is_primary = models.BooleanField(default=False, help_text="Primary account shown first")
    notes = models.TextField(blank=True, help_text="Additional instructions or notes")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_bank_accounts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "-is_active", "bank_name"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_name} ({self.account_number})"


class PaymentInstruction(models.Model):
    """Instructions shown to users for making payments."""
    title = models.CharField(max_length=150, help_text="e.g., Bank Transfer Instructions")
    content = models.TextField(help_text="Step-by-step instructions for users")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-is_active"]

    def __str__(self):
        return self.title