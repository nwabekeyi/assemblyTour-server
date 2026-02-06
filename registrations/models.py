from django.db import models
from django.conf import settings
from django.utils import timezone

# Correct import for Package model
from packages.models import Package


# -----------------------------
# STEP CONFIGURATION (SYSTEM)
# -----------------------------
class StepAction(models.TextChoices):
    FILL_FORM = "fill_form", "Fill Form"
    UPLOAD = "upload", "Upload Files"
    PAYMENT = "payment", "Make Payment"
    REVIEW = "review", "Review & Confirm"
    APPROVAL = "approval", "Admin Approval"
    AUTO = "auto", "System Generated"


class StepDataScope(models.TextChoices):
    USER = "user", "User Profile"
    REGISTRATION = "registration", "Hajj Registration"
    DOCUMENTS = "documents", "Documents"
    PAYMENT = "payment", "Payment"
    HOTEL = "hotel", "Hotel"
    FLIGHT = "flight", "Flight"


class RegistrationStep(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    action_type = models.CharField(
        max_length=20, choices=StepAction.choices, default=StepAction.AUTO
    )
    data_scope = models.CharField(
        max_length=20, choices=StepDataScope.choices, default=StepDataScope.REGISTRATION
    )
    order = models.PositiveIntegerField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}. {self.title}"


# -----------------------------
# REGISTRATION CORE
# -----------------------------
class RegistrationStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not_started"
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class HajjRegistration(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hajj_registration"
    )

    passport_document = models.FileField(
        upload_to='hajj/passports/',
        null=True,
        blank=True
    )
    yellow_card_document = models.FileField(
        upload_to='hajj/yellow_cards/',
        null=True,
        blank=True
    )
    current_step = models.ForeignKey(
        RegistrationStep, on_delete=models.PROTECT, related_name="registrations"
    )
    completed_steps = models.ManyToManyField(
        RegistrationStep, blank=True, related_name="completed_registrations"
    )
    status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.NOT_STARTED
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.PROTECT,
        related_name="registrations",
        null=True,
        blank=True
    )

    # --- Journey & Travel Details (Populated by Admin) ---
    ticket_info = models.TextField(blank=True, null=True, help_text="Flight/Travel details")
    hotel_info = models.TextField(blank=True, null=True, help_text="Accommodation details")
    package_benefits = models.TextField(blank=True, null=True, help_text="Specific benefits for this user")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if not self.user:
            return f"No user – {self.status}"

        if self.user.username:
            return f"{self.user.username} – {self.status}"
    
        if hasattr(self.user, 'email') and self.user.email:
            return f"{self.user.email} – {self.status}"
    
        return f"User #{self.user_id} – {self.status}"


# -----------------------------
# STEP 8: MULTIPLE DOCUMENTS
# -----------------------------
class RegistrationAdditionalDocument(models.Model):
    registration = models.ForeignKey(
        HajjRegistration, 
        on_delete=models.CASCADE, 
        related_name="additional_documents"
    )
    title = models.CharField(max_length=100, help_text="e.g., Visa Copy, Hotel Voucher")
    file = models.FileField(upload_to='hajj_extra_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.registration.user.phone}"


# -----------------------------
# STEP REVIEW / APPROVAL
# -----------------------------
class StepReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class RegistrationStepReview(models.Model):
    registration = models.ForeignKey(
        HajjRegistration, 
        on_delete=models.CASCADE, 
        related_name="step_reviews"
    )
    step = models.ForeignKey(
        RegistrationStep, 
        on_delete=models.CASCADE, 
        related_name="reviews"
    )
    status = models.CharField(
        max_length=20, 
        choices=StepReviewStatus.choices, 
        default=StepReviewStatus.PENDING
    )
    rejection_reason = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name="reviewed_registration_steps"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("registration", "step")
        ordering = ["step__order"]

    def __str__(self):
        return f"{self.registration.user.email} – {self.step.code} – {self.status}"

    def approve(self, user):
        self.status = StepReviewStatus.APPROVED
        self.rejection_reason = ""
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, user, reason: str):
        self.status = StepReviewStatus.REJECTED
        self.rejection_reason = reason
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save()