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


class VisaStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class JourneyPresenceStatus(models.TextChoices):
    PRE_TRAVEL = "pre_travel", "Awaiting Travel"
    IN_MECCA = "in_mecca", "In Destination"
    ARRIVED = "arrived", "Arrived"
    DID_NOT_ARRIVE = "did_not_arrive", "Did Not Arrive"


class Registration(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations"
    )

    passport_document = models.URLField(max_length=500, null=True, blank=True)
    passport_document_public_id = models.CharField(max_length=255, null=True, blank=True)
    yellow_card_document = models.URLField(max_length=500, null=True, blank=True)
    yellow_card_document_public_id = models.CharField(max_length=255, null=True, blank=True)
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
    visa_status = models.CharField(
        max_length=20,
        choices=VisaStatus.choices,
        default=VisaStatus.PENDING,
        help_text="Overall visa readiness status"
    )
    visa_status_notes = models.TextField(blank=True, null=True)

    # --- Journey & Travel Details (Populated by Admin) ---
    ticket_info = models.TextField(blank=True, null=True, help_text="Flight/Travel details")
    hotel_info = models.TextField(blank=True, null=True, help_text="Accommodation details")
    journey_presence_status = models.CharField(
        max_length=20,
        choices=JourneyPresenceStatus.choices,
        default=JourneyPresenceStatus.PRE_TRAVEL,
        help_text="Tracks traveler presence during and after the journey"
    )
    journey_presence_notes = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True, help_text="Reason for cancellation (required)")
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="cancelled_registrations",
        help_text="Admin who cancelled this registration"
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

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
# TRAVEL DOCUMENTS (Uploaded by Admin)
# -----------------------------
class TravelDocumentType(models.TextChoices):
    VISA = "visa", "Visa"
    TICKET = "ticket", "Flight Ticket"
    HOTEL_VOUCHER = "hotel_voucher", "Hotel Voucher"


class TravelDocument(models.Model):
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="travel_documents"
    )
    doc_type = models.CharField(
        max_length=20,
        choices=TravelDocumentType.choices,
        default=TravelDocumentType.VISA
    )
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='travel_documents/')
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_travel_documents"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Visa specific fields (required when doc_type is visa)
    visa_number = models.CharField(max_length=50, blank=True, null=True)
    visa_type = models.CharField(max_length=50, blank=True, null=True)
    visa_issue_date = models.DateField(blank=True, null=True)
    visa_expiry_date = models.DateField(blank=True, null=True)
    visa_country = models.CharField(max_length=100, blank=True, null=True)
    visa_port_of_entry = models.CharField(max_length=100, blank=True, null=True)
    
    # Flight/Ticket specific fields (required when doc_type is ticket)
    airline_name = models.CharField(max_length=100, blank=True, null=True)
    flight_number = models.CharField(max_length=50, blank=True, null=True)
    departure_airport = models.CharField(max_length=100, blank=True, null=True)
    arrival_airport = models.CharField(max_length=100, blank=True, null=True)
    departure_date = models.DateField(blank=True, null=True)
    departure_time = models.TimeField(blank=True, null=True)
    arrival_date = models.DateField(blank=True, null=True)
    arrival_time = models.TimeField(blank=True, null=True)
    seat_number = models.CharField(max_length=20, blank=True, null=True)
    booking_reference = models.CharField(max_length=50, blank=True, null=True)
    
    # Hotel specific fields (required when doc_type is hotel_voucher)
    hotel_name = models.CharField(max_length=200, blank=True, null=True)
    hotel_address = models.TextField(blank=True, null=True)
    room_type = models.CharField(max_length=50, blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    check_in_date = models.DateField(blank=True, null=True)
    check_in_time = models.TimeField(blank=True, null=True)
    check_out_date = models.DateField(blank=True, null=True)
    check_out_time = models.TimeField(blank=True, null=True)
    number_of_nights = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = [("registration", "doc_type")]

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Enforce max 3 documents per registration at DB level
        if self.registration_id:
            current_count = TravelDocument.objects.filter(
                registration_id=self.registration_id
            ).exclude(pk=self.pk).count()
            
            if current_count >= 3:
                raise ValidationError("Maximum of 3 travel documents allowed per registration.")
        
        if self.doc_type == TravelDocumentType.VISA:
            required_fields = ['visa_number', 'visa_type', 'visa_issue_date', 'visa_expiry_date', 'visa_country', 'visa_port_of_entry']
            missing = [f for f in required_fields if not getattr(self, f)]
            if missing:
                raise ValidationError(f"Visa details require: {', '.join(missing).replace('_', ' ').title()}")
        elif self.doc_type == TravelDocumentType.TICKET:
            required_fields = ['airline_name', 'flight_number', 'departure_airport', 'arrival_airport', 'departure_date', 'arrival_date', 'seat_number']
            missing = [f for f in required_fields if not getattr(self, f)]
            if missing:
                raise ValidationError(f"Ticket details require: {', '.join(missing).replace('_', ' ').title()}")
        elif self.doc_type == TravelDocumentType.HOTEL_VOUCHER:
            required_fields = ['hotel_name', 'hotel_address', 'room_type', 'room_number', 'check_in_date', 'check_out_date', 'number_of_nights']
            missing = [f for f in required_fields if not getattr(self, f)]
            if missing:
                raise ValidationError(f"Hotel details require: {', '.join(missing).replace('_', ' ').title()}")
        super().clean()


# -----------------------------
# PAYMENT DETAILS (Uploaded by User)
# -----------------------------
class PaymentDetail(models.Model):
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="payment_details"
    )
    title = models.CharField(max_length=100, help_text="e.g., Bank Transfer Receipt, Payment Proof")
    file = models.FileField(upload_to='payment_details/')
    description = models.TextField(blank=True, help_text="Additional notes about the payment")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_payment_details"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("registration", "title")]

    def __str__(self):
        return f"{self.registration.user.email} - {self.title}"


# -----------------------------
# STEP 8: MULTIPLE DOCUMENTS
# -----------------------------
class RegistrationAdditionalDocument(models.Model):
    registration = models.ForeignKey(
        Registration, 
        on_delete=models.CASCADE, 
        related_name="additional_documents"
    )
    title = models.CharField(max_length=100, help_text="e.g., Visa Copy, Hotel Voucher")
    file = models.FileField(upload_to='hajj_extra_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration.user.email} - {self.title}"


# -----------------------------
# STEP REVIEW / APPROVAL
# -----------------------------
class StepReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class RegistrationStepReview(models.Model):
    registration = models.ForeignKey(
        Registration, 
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


class UserDashboardStats(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_stats"
    )
    total_travels = models.PositiveIntegerField(default=0)
    in_progress_travels = models.PositiveIntegerField(default=0)
    completed_travels = models.PositiveIntegerField(default=0)
    failed_travels = models.PositiveIntegerField(default=0)
    last_refresh = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Dashboard Stat"
        verbose_name_plural = "User Dashboard Stats"

    def __str__(self):
        return f"Stats for {self.user}"


# -----------------------------
# USER SUPPORT TICKETS
# -----------------------------
class SupportTicketStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    PENDING = "pending", "Pending User Reply"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"


class SupportTicketCategory(models.TextChoices):
    REGISTRATION = "registration", "Registration"
    PAYMENT = "payment", "Payment"
    DOCUMENTS = "documents", "Documents"
    TRAVEL = "travel", "Travel Info"
    VISA = "visa", "Visa"
    OTHER = "other", "Other"


class SupportTicket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets"
    )
    registration = models.ForeignKey(
        Registration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets"
    )
    category = models.CharField(
        max_length=20,
        choices=SupportTicketCategory.choices,
        default=SupportTicketCategory.OTHER
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=SupportTicketStatus.choices,
        default=SupportTicketStatus.OPEN
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets"
    )
    resolved_response = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_tickets"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.id} - {self.subject} - {self.user.email}"


class SupportTicketReply(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="replies"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ticket_replies"
    )
    message = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="Admin-only internal notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply to #{self.ticket.id} by {self.user.email}"


# -----------------------------
# MANASIK GUIDANCE (Admin Posted)
# -----------------------------
class ManasikGuidanceType(models.TextChoices):
    IHRAM = "ihram", "Ihram Guide"
    TAWAF = "tawaf", "Tawaf & Sa'i"
    DUA = "dua", "Dua & Prayers"
    GENERAL = "general", "General Guide"


class ManasikGuidance(models.Model):
    title = models.CharField(max_length=200)
    guidance_type = models.CharField(
        max_length=20,
        choices=ManasikGuidanceType.choices,
        default=ManasikGuidanceType.GENERAL
    )
    content = models.TextField()
    icon = models.CharField(max_length=10, default="📖")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.title} ({self.guidance_type})"


# -----------------------------
# EMERGENCY CONTACTS
# -----------------------------
class ContactType(models.TextChoices):
    PHONE = "phone", "Phone"
    WHATSAPP = "whatsapp", "WhatsApp"
    EMAIL = "email", "Email"
    TELEGRAM = "telegram", "Telegram"


class EmergencyContact(models.Model):
    name = models.CharField(max_length=100)
    contact_type = models.CharField(
        max_length=20,
        choices=ContactType.choices
    )
    value = models.CharField(max_length=200)
    description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.name} - {self.contact_type}: {self.value}"
