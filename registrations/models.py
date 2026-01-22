from django.db import models
from django.conf import settings


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
    VISA = "visa", "Visa"
    HOTEL = "hotel", "Hotel"
    FLIGHT = "flight", "Flight"


class RegistrationStep(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Internal step key (e.g. details, documents, payment)"
    )

    title = models.CharField(
        max_length=100,
        help_text="Short title shown to users"
    )

    description = models.TextField(
        help_text="What the user needs to do in this step"
    )

    action_type = models.CharField(
        max_length=20,
        choices=StepAction.choices,
        default=StepAction.AUTO,
        help_text="Type of action required in this step"
    )

    data_scope = models.CharField(
        max_length=20,
        choices=StepDataScope.choices,
        default=StepDataScope.REGISTRATION,
        help_text="Which part of the system this step works on"
    )

    order = models.PositiveIntegerField(
        unique=True,
        help_text="Step order (1, 2, 3...)"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}. {self.title}"


class RegistrationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class HajjRegistration(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hajj_registration"
    )

    current_step = models.ForeignKey(
        RegistrationStep,
        on_delete=models.PROTECT,
        related_name="registrations"
    )

    completed_steps = models.ManyToManyField(
        RegistrationStep,
        blank=True,
        related_name="completed_by_users"
    )

    status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.PENDING,
        help_text="Overall registration status"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.email} – {self.status.title()}"

    @property
    def is_completed(self) -> bool:
        """
        Returns True if all active steps are completed.
        """
        total_steps = RegistrationStep.objects.filter(is_active=True).count()
        return self.completed_steps.count() >= total_steps

    def update_status(self):
        """
        Update registration status based on completed steps.
        """
        if self.is_completed:
            self.status = RegistrationStatus.COMPLETED
        elif self.status != RegistrationStatus.FAILED:
            self.status = RegistrationStatus.PENDING
        self.save()
