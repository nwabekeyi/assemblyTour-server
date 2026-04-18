from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.files.storage import default_storage
from django.utils import timezone
from django.utils.html import format_html
from django.contrib.auth import get_user_model
import json
from .models import (
    RegistrationStep,
    RegistrationStatus,
    StepReviewStatus,
    VisaStatus,
    JourneyPresenceStatus,
    Registration,
    RegistrationStepReview,
    TravelDocument,
    TravelDocumentType,
    SupportTicket,
    SupportTicketReply,
    ManasikGuidance,
    EmergencyContact,
    PaymentDetail,
)
from .services import complete_travel_documents_step
from core.services.email_service import (
    send_step_approved_email,
    send_step_rejected_email,
    notify_admins_of_registration_event,
)

User = get_user_model()

# -----------------------------
# RegistrationStepAdmin
# -----------------------------
@admin.register(RegistrationStep)
class RegistrationStepAdmin(admin.ModelAdmin):
    list_display = ("order", "code", "title", "action_type", "data_scope", "is_active")
    readonly_fields = [f.name for f in RegistrationStep._meta.fields]

    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False


class RegistrationAdminForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        presence_status = cleaned.get("journey_presence_status")
        notes = cleaned.get("journey_presence_notes")
        if presence_status == JourneyPresenceStatus.DID_NOT_ARRIVE and not notes:
            raise forms.ValidationError("Please add notes describing the incident when marking 'Did Not Arrive'.")
        return cleaned


# -----------------------------
# TravelDocument Inline
# -----------------------------
class TravelDocumentForm(forms.ModelForm):
    class Meta:
        model = TravelDocument
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get existing doc types for this registration
        existing_doc_types = []
        if self.instance and self.instance.registration_id:
            existing_doc_types = list(
                TravelDocument.objects.filter(
                    registration_id=self.instance.registration_id
                ).values_list('doc_type', flat=True)
            )
        
        # Filter out already added doc types
        available_choices = [
            (choice[0], choice[1]) 
            for choice in TravelDocumentType.choices 
            if choice[0] not in existing_doc_types
        ]
        
        self.fields['doc_type'].choices = [('', '-----------')] + available_choices
        
        for field_name in ['visa_number', 'visa_type', 'visa_issue_date', 'visa_expiry_date', 
                           'visa_country', 'visa_port_of_entry', 'airline_name', 'flight_number',
                           'departure_airport', 'arrival_airport', 'departure_date', 'departure_time',
                           'arrival_date', 'arrival_time', 'seat_number', 'booking_reference',
                           'hotel_name', 'hotel_address', 'room_type', 'room_number',
                           'check_in_date', 'check_in_time', 'check_out_date', 'check_out_time',
                           'number_of_nights']:
            self.fields[field_name].required = False
        
        self.fields['seat_number'].widget.attrs.update({'type': 'number', 'min': '1', 'max': '999'})
        self.fields['number_of_nights'].widget.attrs.update({'type': 'number', 'min': '1', 'max': '365'})
        self.fields['departure_date'].widget.attrs.update({'type': 'date'})
        self.fields['arrival_date'].widget.attrs.update({'type': 'date'})
        self.fields['check_in_date'].widget.attrs.update({'type': 'date'})
        self.fields['check_out_date'].widget.attrs.update({'type': 'date'})
        self.fields['visa_issue_date'].widget.attrs.update({'type': 'date'})
        self.fields['visa_expiry_date'].widget.attrs.update({'type': 'date'})
        self.fields['departure_time'].widget.attrs.update({'type': 'time'})
        self.fields['arrival_time'].widget.attrs.update({'type': 'time'})
        self.fields['check_in_time'].widget.attrs.update({'type': 'time'})
        self.fields['check_out_time'].widget.attrs.update({'type': 'time'})

    def clean(self):
        cleaned_data = super().clean()
        doc_type = cleaned_data.get('doc_type')
        
        # Skip validation if no doc_type selected
        if not doc_type:
            return cleaned_data
        
        # Only validate required fields for the selected doc_type
        if doc_type == 'visa':
            required_fields = {
                'visa_number': 'Visa Number',
                'visa_type': 'Visa Type',
                'visa_issue_date': 'Visa Issue Date',
                'visa_expiry_date': 'Visa Expiry Date',
                'visa_country': 'Visa Country',
                'visa_port_of_entry': 'Port of Entry'
            }
            missing = [label for field, label in required_fields.items() if not cleaned_data.get(field)]
            if missing:
                raise forms.ValidationError(f"Visa details required: {', '.join(missing)}")
        elif doc_type == 'ticket':
            required_fields = {
                'airline_name': 'Airline Name',
                'flight_number': 'Flight Number',
                'departure_airport': 'Departure Airport',
                'arrival_airport': 'Arrival Airport',
                'departure_date': 'Departure Date',
                'arrival_date': 'Arrival Date',
                'seat_number': 'Seat Number'
            }
            missing = [label for field, label in required_fields.items() if not cleaned_data.get(field)]
            if missing:
                raise forms.ValidationError(f"Flight details required: {', '.join(missing)}")
        elif doc_type == 'hotel_voucher':
            required_fields = {
                'hotel_name': 'Hotel Name',
                'hotel_address': 'Hotel Address',
                'room_type': 'Room Type',
                'room_number': 'Room Number',
                'check_in_date': 'Check-in Date',
                'check_out_date': 'Check-out Date',
                'number_of_nights': 'Number of Nights'
            }
            missing = [label for field, label in required_fields.items() if not cleaned_data.get(field)]
            if missing:
                raise forms.ValidationError(f"Hotel details required: {', '.join(missing)}")
        
        return cleaned_data


class TravelDocumentInline(admin.StackedInline):
    model = TravelDocument
    extra = 0
    max_num = 3
    form = TravelDocumentForm
    readonly_fields = ("uploaded_by", "uploaded_at")
    min_num = 0
    
    def has_add_permission(self, request, obj=None):
        if obj and obj.visa_status != VisaStatus.READY:
            return False
        if obj and obj.travel_documents.count() >= 3:
            return False
        return True
    
    def get_extra(self, request, obj, **kwargs):
        if not obj:
            return 0
        if obj.visa_status != VisaStatus.READY:
            return 0
        if obj.travel_documents.count() >= 3:
            return 0
        return 1
    
    def get_max_num(self, request, obj, **kwargs):
        return 3

    def has_change_permission(self, request, obj=None):
        if obj and obj.visa_status != VisaStatus.READY:
            return False
        return super().has_change_permission(request, obj)

    def has_view_permission(self, request, obj=None):
        if obj and obj.visa_status != VisaStatus.READY:
            return False
        return super().has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.visa_status != VisaStatus.READY:
            return False
        return super().has_delete_permission(request, obj)

    def get_extra(self, request, obj=None):
        # Allow adding new documents
        if not obj:
            return 0
        if obj.visa_status != VisaStatus.READY:
            return 0
        return 1

    def get_max_num(self, request, obj=None):
        return None

    def get_fieldsets(self, request, obj=None):
        return [
            (None, {'fields': ('doc_type', 'title', 'file', 'description')}),
            ('Visa Details (fill if visa)', {'fields': ('visa_number', 'visa_type', 'visa_issue_date', 'visa_expiry_date', 'visa_country', 'visa_port_of_entry'), 'classes': ('collapse',)}),
            ('Flight Details (fill if ticket)', {'fields': ('airline_name', 'flight_number', 'departure_airport', 'arrival_airport', 'departure_date', 'departure_time', 'arrival_date', 'arrival_time', 'seat_number', 'booking_reference'), 'classes': ('collapse',)}),
            ('Hotel Details (fill if hotel)', {'fields': ('hotel_name', 'hotel_address', 'room_type', 'room_number', 'check_in_date', 'check_in_time', 'check_out_date', 'check_out_time', 'number_of_nights'), 'classes': ('collapse',)}),
            ('Metadata', {'fields': ('uploaded_by', 'uploaded_at')})
        ]

    def get_formset(self, request, obj=None):
        formset = super().get_formset(request, obj)
        
        if not obj:
            return formset
        
        used_types = set(obj.travel_documents.values_list('doc_type', flat=True))
        
        original_init = formset.form.__init__

        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Get all available doc types
            available_choices = list(TravelDocumentType.choices)
            
            if hasattr(self, 'instance') and self.instance and self.instance.pk:
                # This is an existing document - show its current type as selected
                current_type = self.instance.doc_type
                self.fields['doc_type'].choices = available_choices
                self.fields['doc_type'].initial = current_type
                self.fields['doc_type'].widget.attrs['readonly'] = True
            else:
                # This is a new document - only show unused types
                unused_choices = [('', '-----------')] + [c for c in TravelDocumentType.choices if c[0] not in used_types]
                self.fields['doc_type'].choices = unused_choices
                
                if len(used_types) >= 3:
                    self.fields['doc_type'].widget.attrs['disabled'] = True
                    self.fields['doc_type'].help_text = "All 3 document types have been uploaded."
                elif len(used_types) == 2:
                    remaining = [c for c in TravelDocumentType.choices if c[0] not in used_types]
                    if remaining:
                        self.fields['doc_type'].initial = remaining[0][0]
                        self.fields['doc_type'].help_text = f"Only {remaining[0][1]} remains to complete step 6."

        formset.form.__init__ = new_init
        return formset

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        
        from django.core.exceptions import ValidationError
        errors = {}
        
        # Get original doc_type if this is an update
        original_doc_type = None
        if change and obj.pk:
            original_doc_type = TravelDocument.objects.get(pk=obj.pk).doc_type
        
        # Only validate if it's a new doc OR doc_type was changed
        if not change or (original_doc_type != obj.doc_type):
            if obj.doc_type == 'visa':
                required = ['visa_number', 'visa_type', 'visa_issue_date', 'visa_expiry_date', 'visa_country', 'visa_port_of_entry']
                for field in required:
                    if not getattr(obj, field):
                        errors[field] = f"{field.replace('_', ' ').title()} is required for visa"
            elif obj.doc_type == 'ticket':
                required = ['airline_name', 'flight_number', 'departure_airport', 'arrival_airport', 'departure_date', 'arrival_date', 'seat_number']
                for field in required:
                    if not getattr(obj, field):
                        errors[field] = f"{field.replace('_', ' ').title()} is required for flight ticket"
            elif obj.doc_type == 'hotel_voucher':
                required = ['hotel_name', 'hotel_address', 'room_type', 'room_number', 'check_in_date', 'check_out_date', 'number_of_nights']
                for field in required:
                    if not getattr(obj, field):
                        errors[field] = f"{field.replace('_', ' ').title()} is required for hotel voucher"
        
        if errors:
            raise ValidationError(errors)
        
        existing = obj.registration.travel_documents.filter(doc_type=obj.doc_type).first()
        if existing:
            if obj.pk:
                obj.pk = existing.pk
            else:
                raise ValidationError(f"A {obj.get_doc_type_display()} document already exists for this registration.")
        
        # Check BEFORE save - if there are 2 docs, this will be the 3rd
        current_count = obj.registration.travel_documents.count()
        is_third_doc = current_count == 2  # This will be the 3rd after save
        
        super(TravelDocumentInline, self).save_model(request, obj, form, change)
        
        # AFTER save, check if we now have exactly 3 documents and trigger transition
        reg = obj.registration
        doc_count = reg.travel_documents.count()
        
        if doc_count == 3:
            print(f"DEBUG: 3 documents uploaded for registration {reg.id}. Completing travel documents step.")
            try:
                result = complete_travel_documents_step(reg)
                reg.refresh_from_db()
                print(f"DEBUG: complete_travel_documents_step result: {result}, current_step: {reg.current_step}")
            except Exception as e:
                print(f"ERROR completing travel documents step: {e}")
        
        # Update ticket and hotel info from travel documents
        ticket_doc = reg.travel_documents.filter(doc_type='ticket').first()
        hotel_doc = reg.travel_documents.filter(doc_type='hotel_voucher').first()
        
        if ticket_doc:
            ticket_info = {
                "airline_name": ticket_doc.airline_name,
                "flight_number": ticket_doc.flight_number,
                "departure_airport": ticket_doc.departure_airport,
                "arrival_airport": ticket_doc.arrival_airport,
                "departure_date": str(ticket_doc.departure_date) if ticket_doc.departure_date else None,
                "arrival_date": str(ticket_doc.arrival_date) if ticket_doc.arrival_date else None,
                "seat_number": ticket_doc.seat_number,
                "booking_reference": ticket_doc.booking_reference,
            }
            reg.ticket_info = json.dumps(ticket_info)
        
        if hotel_doc:
            hotel_info = {
                "hotel_name": hotel_doc.hotel_name,
                "hotel_address": hotel_doc.hotel_address,
                "room_type": hotel_doc.room_type,
                "room_number": hotel_doc.room_number,
                "check_in_date": str(hotel_doc.check_in_date) if hotel_doc.check_in_date else None,
                "check_out_date": str(hotel_doc.check_out_date) if hotel_doc.check_out_date else None,
                "number_of_nights": hotel_doc.number_of_nights,
            }
            reg.hotel_info = json.dumps(hotel_info)
        
        # Use transaction.on_commit to ensure this runs after all saves complete
        from django.db import transaction
        transaction.on_commit(lambda: reg.save(update_fields=['ticket_info', 'hotel_info', 'current_step', 'status', 'updated_at']))


# -----------------------------
# PaymentDetail Inline
# -----------------------------
class PaymentDetailInline(admin.StackedInline):
    model = PaymentDetail
    extra = 0
    max_num = 1
    readonly_fields = ("uploaded_by", "uploaded_at")
    fields = ("title", "file", "description", "uploaded_by", "uploaded_at")

    def has_delete_permission(self, request, obj=None): return True
    def has_add_permission(self, request, obj=None): return True

    def get_extra(self, request, obj=None):
        if obj and obj.payment_details.exists():
            return 0  # Don't show extra forms if one already exists
        return 1

    def formfield_for_dbfsfsfsfsf(self, db_field, request, **kwargs):
        if db_field.name == "title":
            # Limit to common payment proof types
            kwargs["queryset"] = PaymentDetail.objects.none()  # We'll show all existing ones
        return super(PaymentDetailInline, self).formfield_for_dbfsfsfsfsf(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super(PaymentDetailInline, self).save_model(request, obj, form, change)


# -----------------------------
# RegistrationStepReview Inline
# -----------------------------
class RegistrationStepReviewInline(admin.TabularInline):
    model = RegistrationStepReview
    extra = 0
    readonly_fields = ("step", "status", "rejection_reason", "reviewed_by", "reviewed_at")


# -----------------------------
# Registration Admin
# -----------------------------
@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    form = RegistrationAdminForm
    list_display = ("get_user_display", "get_current_step_display", "status", "visa_status", "updated_at")
    list_filter = ("status", "visa_status", "current_step")
    search_fields = ("user__username", "user__email", "user__phone")
    inlines = [TravelDocumentInline]
    readonly_fields = (
        "user", "package", "current_step", "status", "completed_steps",
        "get_user_bio_summary", "get_passport_preview", "get_yellow_card_preview",
        "get_travel_documents_list", "get_payment_proof_preview", "get_payment_review_status",
        "get_user_profile_picture_metadata", "get_registration_documents_metadata",
        "get_account_summary", "get_visa_status_display", "get_journey_status_display",
        "cancellation_reason", "cancelled_by", "cancelled_at",
        "created_at", "updated_at"
    )

    change_form_template = "admin/hajjregistration_change_form.html"

    def changeview(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj and obj.journey_presence_status in [JourneyPresenceStatus.ARRIVED, JourneyPresenceStatus.IN_MECCA]:
            extra_context['can_cancel'] = False
        else:
            extra_context['can_cancel'] = True
        return super().changeview(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        if "_cancel_registration" in request.POST:
            reason = request.POST.get("cancellation_reason", "").strip()
            if not reason:
                from django.contrib import messages
                self.message_user(request, "Cancellation reason is required.", messages.ERROR)
                return super().response_change(request, obj)
            
            obj.status = RegistrationStatus.FAILED
            obj.cancellation_reason = reason
            obj.cancelled_by = request.user
            from django.utils import timezone
            obj.cancelled_at = timezone.now()
            obj.save(update_fields=["status", "cancellation_reason", "cancelled_by", "cancelled_at", "updated_at"])
            from django.contrib import messages
            self.message_user(request, f"Registration cancelled for {obj.user}.", messages.SUCCESS)
            return super().response_change(request, obj)
        return super().response_change(request, obj)

    def get_inlines(self, request, obj):
        if obj and obj.visa_status == VisaStatus.READY:
            return [TravelDocumentInline]
        return []

    # -----------------------------
    # Fieldsets
    # -----------------------------
    def get_fieldsets(self, request, obj=None):
        # Core Progress - read-only (excludes visa_status and journey_presence_status)
        fieldsets = [
            ("Core Progress", {
                "fields": ("user", "package", "current_step", "status", "completed_steps"),
                "description": "This section is read-only."
            }),
        ]

        if obj:
            # Step 1: Account Setup
            account_step = RegistrationStep.objects.filter(code="account_setup").first()
            if account_step:
                account_review = obj.step_reviews.filter(step=account_step).first()
                if not account_review or account_review.status == "pending":
                    fieldsets.append(("Step 1: Account Setup", {
                        "fields": ("get_account_summary",),
                        "description": "Account setup pending. Approve below."
                    }))
                elif account_review.status == "approved":
                    fieldsets.append(("Step 1: Account Approved", {
                        "fields": ("get_account_summary",),
                    }))

            # Step 2: User Bio
            if obj.current_step.code == "registration_form":
                fieldsets.append(("Step 2: User Bio", {
                    "fields": ("get_user_bio_summary",),
                    "description": "Step in progress. Approve or Reject below."
                }))
            elif obj.completed_steps.filter(code="registration_form").exists():
                fieldsets.append(("Step 2: Approved Bio-Data", {
                    "fields": ("get_user_bio_summary",),
                }))

            # Step 3: Payment Details
            payment_step = RegistrationStep.objects.filter(code="payment_details").first()
            if payment_step:
                payment_review = obj.step_reviews.filter(step=payment_step).first()
                payment_uploaded = obj.payment_details.exists()
                
                if payment_uploaded:
                    if not payment_review or payment_review.status == "pending":
                        fieldsets.append(("Step 3: Payment Details", {
                            "fields": ("get_payment_proof_preview", "get_payment_review_status"),
                            "description": "Payment uploaded. Approve or Reject below."
                        }))
                    elif payment_review.status == "approved":
                        fieldsets.append(("Step 3: Payment Approved", {
                            "fields": ("get_payment_proof_preview",),
                        }))

            # Step 4: Documents
            if obj.completed_steps.filter(code="document_upload").exists():
                fieldsets.append(("Step 4: User Documents", {
                    "fields": ("get_passport_preview", "get_yellow_card_preview"),
                    "description": "Documents uploaded. Approve or Reject below."
                }))

            # Visa Status - only show if user has uploaded both passport and yellow card AND they have been approved
            has_passport = bool(obj.passport_document)
            has_yellow_card = bool(obj.yellow_card_document)
            document_step = RegistrationStep.objects.filter(code="document_upload").first()
            document_review = obj.step_reviews.filter(step=document_step).first() if document_step else None
            document_upload_approved = document_review and document_review.status == StepReviewStatus.APPROVED
            if has_passport and has_yellow_card and document_upload_approved:
                fieldsets.append(("Visa Status", {
                    "fields": ("visa_status", "visa_status_notes"),
                    "description": "Update visa status here."
                }))

            # Travel Documents
            fieldsets.append(("Travel Documents", {
                "fields": ("get_travel_documents_list",),
                "description": "Review travel documents using inline below."
            }))

            # Arrival Status - only show if admin has uploaded all 3 travel documents (visa, ticket, hotel_voucher)
            required_doc_types = {"visa", "ticket", "hotel_voucher"}
            uploaded_doc_types = set(obj.travel_documents.values_list("doc_type", flat=True))
            if required_doc_types.issubset(uploaded_doc_types):
                fieldsets.append(("Arrival Status", {
                    "fields": ("journey_presence_status", "journey_presence_notes"),
                    "description": "Update journey presence status."
                }))

            # System metadata
            fieldsets.append(("System Metadata", {
                "fields": (
                    "get_user_profile_picture_metadata",
                    "get_registration_documents_metadata",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",)
            }))

        return fieldsets

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        obj = self.get_object(request, object_id)
        if obj and obj.journey_presence_status == JourneyPresenceStatus.ARRIVED:
            extra_context['show_save'] = False
            extra_context['show_save_as_new'] = False
        if obj and obj.journey_presence_status in [JourneyPresenceStatus.ARRIVED, JourneyPresenceStatus.IN_MECCA]:
            extra_context['can_cancel'] = False
        else:
            extra_context['can_cancel'] = True
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._handle_visa_status_transition(request, obj)
        self._handle_travel_documents_transition(request, obj)
        self._handle_journey_presence_transition(request, obj)

    def has_delete_permission(self, request):
        obj = getattr(request, '_admin_obj', None)
        if obj and obj.journey_presence_status == JourneyPresenceStatus.ARRIVED:
            return False
        return super().has_delete_permission(request)

    # -----------------------------
    # Payment Proof Preview
    # -----------------------------
    def get_payment_proof_preview(self, obj):
        payment = obj.payment_details.first()
        if payment and payment.file:
            url = payment.file.url if hasattr(payment.file, 'url') else str(payment.file)
            return format_html(
                '<a href="{0}" target="_blank" class="button" style="background:#447e9b; color:white; padding:4px 8px;">Open Payment Proof</a>',
                url
            )
        return "No payment proof uploaded"

    def get_payment_review_status(self, obj):
        payment_step = RegistrationStep.objects.filter(code="payment_details").first()
        if not payment_step:
            return "Step not found"
        review = obj.step_reviews.filter(step=payment_step).first()
        if not review:
            return "Not submitted"
        status_map = {
            "pending": "Awaiting Review",
            "approved": "Approved",
            "rejected": f"Rejected: {review.rejection_reason or 'No reason'}"
        }
        return status_map.get(review.status, review.status)

    def get_user_profile_picture_metadata(self, obj):
        profile_picture = getattr(obj.user, "profile_picture", None)
        if not profile_picture:
            return "No profile picture uploaded"

        if profile_picture.startswith(("http://", "https://")):
            return format_html(
                '<a href="{0}" target="_blank" class="button" style="background:#447e9b; color:white; padding:4px 8px;">Open Profile Picture</a>',
                profile_picture
            )

        return profile_picture
    get_user_profile_picture_metadata.short_description = "Profile Picture (User)"

    def get_registration_documents_metadata(self, obj):
        return format_html(
            "<b>Passport URL:</b> {}<br>"
            "<b>Passport Public ID:</b> {}<br>"
            "<b>Yellow Card URL:</b> {}<br>"
            "<b>Yellow Card Public ID:</b> {}",
            obj.passport_document or "-",
            obj.passport_document_public_id or "-",
            obj.yellow_card_document or "-",
            obj.yellow_card_document_public_id or "-",
        )
    get_registration_documents_metadata.short_description = "Uploaded Document Metadata"

    def _handle_visa_status_transition(self, request, obj):
        if not obj:
            return

        step = RegistrationStep.objects.filter(code="visa_status").first()
        if not step:
            return

        if obj.visa_status == VisaStatus.READY:
            if not obj.completed_steps.filter(pk=step.pk).exists():
                obj.completed_steps.add(step)
                next_step = RegistrationStep.objects.filter(
                    order__gt=step.order,
                    is_active=True
                ).order_by('order').first()

                if next_step:
                    obj.current_step = next_step

                if obj.status == RegistrationStatus.FAILED:
                    obj.status = RegistrationStatus.PENDING

                obj.save(update_fields=["current_step", "status", "updated_at"])
                self.message_user(
                    request,
                    "Visa marked as ready. Registration advanced to the next step.",
                    messages.SUCCESS
                )
        elif obj.visa_status == VisaStatus.FAILED:
            obj.status = RegistrationStatus.FAILED
            obj.save(update_fields=["status", "updated_at"])
            self.message_user(
                request,
                "Visa marked as failed. Registration set to failed.",
                messages.ERROR
            )

    def _handle_travel_documents_transition(self, request, obj):
        if not obj:
            return

        step = RegistrationStep.objects.filter(code="travel_documents").first()
        if not step:
            return

        # Refresh from DB to get latest travel documents
        obj.refresh_from_db()
        
        required_types = ["visa", "ticket", "hotel_voucher"]
        uploaded_types = set(obj.travel_documents.values_list("doc_type", flat=True))
        
        missing_types = [t for t in required_types if t not in uploaded_types]
        
        if missing_types:
            return

        if obj.completed_steps.filter(pk=step.pk).exists():
            return

        obj.completed_steps.add(step)
        
        next_step = RegistrationStep.objects.filter(
            order__gt=step.order,
            is_active=True
        ).order_by('order').first()

        if next_step:
            obj.current_step = next_step

        obj.save(update_fields=["current_step", "updated_at"])
        print(f"RegistrationAdmin: Travel docs complete, moved to {next_step}")
        self.message_user(
            request,
            "Travel documents completed! Registration advanced to the next step.",
            messages.SUCCESS
        )

    def _handle_journey_presence_transition(self, request, obj):
        if not obj:
            return

        step = RegistrationStep.objects.filter(code="arrival_status").first()
        state = obj.journey_presence_status

        if state == JourneyPresenceStatus.IN_MECCA:
            if obj.status == RegistrationStatus.NOT_STARTED:
                obj.status = RegistrationStatus.PENDING
            obj.save(update_fields=["status", "journey_presence_status", "updated_at"])
            self.message_user(
                request,
                "Pilgrim marked as currently in Mecca.",
                messages.SUCCESS
            )
        elif state == JourneyPresenceStatus.ARRIVED:
            if step and not obj.completed_steps.filter(pk=step.pk).exists():
                obj.completed_steps.add(step)
            obj.status = RegistrationStatus.COMPLETED
            obj.save(update_fields=["status", "journey_presence_status", "updated_at"])
            self.message_user(
                request,
                "Pilgrim marked as arrived and registration completed.",
                messages.SUCCESS
            )
        elif state == JourneyPresenceStatus.DID_NOT_ARRIVE:
            if step and not obj.completed_steps.filter(pk=step.pk).exists():
                obj.completed_steps.add(step)
            obj.status = RegistrationStatus.FAILED
            obj.save(update_fields=["status", "journey_presence_status", "updated_at"])
            self.message_user(
                request,
                "Incident recorded. Registration marked as 'Did Not Arrive'.",
                messages.ERROR
            )

    # -----------------------------
    # User Bio Display
    # -----------------------------
    def get_user_bio_summary(self, obj):
        u = obj.user
        name = " ".join(filter(None, [u.first_name, u.last_name])) or u.username or u.email or u.phone
        
        # Profile picture button - must be valid Cloudinary URL
        profile_html = ""
        pic = u.profile_picture
        if pic and (pic.startswith('http://') or pic.startswith('https://')):
            profile_html = format_html(
                '<div style="margin-bottom:15px;"><a href="{}" target="_blank" class="button" style="background:#447e9b; color:white; padding:4px 8px;">Open Profile Picture</a></div>',
                pic
            )
        
        # Format passport expiry date if exists
        passport_expiry = str(u.passport_expiry) if u.passport_expiry else "-"
        
        bio_html = format_html(
            "<b>Name:</b> {}<br>"
            "<b>Phone:</b> {}<br>"
            "<b>Email:</b> {}<br>"
            "<b>Gender:</b> {}<br>"
            "<b>Date of Birth:</b> {}<br>"
            "<b>Nationality:</b> {}<br>"
            "<b>State of Origin:</b> {}<br>"
            "<b>Passport #:</b> {}<br>"
            "<b>Passport Expiry:</b> {}<br>"
            "<b>Address:</b> {}<br>"
            "<b>Emergency Contact Name:</b> {}<br>"
            "<b>Emergency Contact Phone:</b> {}",
            name,
            u.phone,
            u.email or "-",
            u.gender.capitalize() if u.gender else "-",
            u.date_of_birth or "-",
            u.nationality or "-",
            u.state_of_origin or "-",
            u.passport_number or "-",
            passport_expiry,
            u.address or "-",
            u.emergency_contact_name or "-",
            u.emergency_contact_phone or "-"
        )
        
        return format_html("{}<br>{}", profile_html, bio_html)
    get_user_bio_summary.short_description = "User Bio"

    # -----------------------------
    # Approve / Reject Steps
    # -----------------------------
    def _get_approval_admin_emails(self):
        admins = User.objects.filter(can_approve_registrations=True, is_active=True)
        return [a.email for a in admins if a.email]

    def _send_user_notification(self, obj, step_title, approved=True, rejection_reason=""):
        user = obj.user
        if not user.email:
            return
        try:
            if approved:
                send_step_approved_email(user.email, step_title, obj.id)
            else:
                send_step_rejected_email(user.email, step_title, obj.id)
        except Exception:
            pass

    def response_change(self, request, obj):
        # Step 2 - registration_form approval - move to step 3
        if "_approve_step2" in request.POST:
            step = obj.current_step
            review, _ = RegistrationStepReview.objects.get_or_create(
                registration=obj,
                step=step,
                defaults={"reviewed_by": request.user}
            )
            review.approve(request.user)
            
            obj.completed_steps.add(step)
            obj.status = RegistrationStatus.PENDING
            
            next_step = RegistrationStep.objects.filter(
                order__gt=step.order,
                is_active=True,
            ).order_by('order').first()
            
            if next_step:
                obj.current_step = next_step
            
            obj.save()
            self._send_user_notification(obj, step.title, approved=True)
            self.message_user(request, "Bio-data approved! User moved to document upload step.", messages.SUCCESS)
            return super().response_change(request, obj)

        # Step 3 - document_upload approval - move to document_review
        if "_approve_document_upload" in request.POST:
            step = RegistrationStep.objects.filter(code="document_upload").first()
            if not step:
                self.message_user(request, "Document upload step not found", messages.ERROR)
                return super().response_change(request, obj)
            
            # Mark document_upload as complete
            if not obj.completed_steps.filter(pk=step.pk).exists():
                obj.completed_steps.add(step)
            
            # Create or update review
            review, _ = RegistrationStepReview.objects.get_or_create(
                registration=obj,
                step=step,
                defaults={
                    "status": StepReviewStatus.APPROVED,
                    "reviewed_by": request.user,
                    "reviewed_at": timezone.now()
                }
            )
            if review.status != StepReviewStatus.APPROVED:
                review.status = StepReviewStatus.APPROVED
                review.reviewed_by = request.user
                review.reviewed_at = timezone.now()
                review.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
            
            # Move to next step (document_review)
            next_step = RegistrationStep.objects.filter(
                order__gt=step.order,
                is_active=True
            ).order_by('order').first()
            
            if next_step:
                obj.current_step = next_step
            
            obj.save()
            self._send_user_notification(obj, step.title, approved=True)
            self.message_user(request, "Documents approved! User moved to next step.", messages.SUCCESS)
            return super().response_change(request, obj)

        # Step 3 - document_upload rejection
        if "_reject_document_upload" in request.POST:
            reason = request.POST.get("reason", "").strip()
            if not reason:
                self.message_user(request, "Rejection reason is required.", messages.ERROR)
                return super().response_change(request, obj)
            
            step = RegistrationStep.objects.filter(code="document_upload").first()
            if not step:
                self.message_user(request, "Document upload step not found", messages.ERROR)
                return super().response_change(request, obj)
            
            # Delete documents from Cloudinary and DB
            from core.services.cloudinary_service import CloudinaryService
            cloudinary_service = CloudinaryService()
            
            if obj.passport_document_public_id:
                try:
                    cloudinary_service.delete(obj.passport_document_public_id)
                except Exception:
                    pass
            
            if obj.yellow_card_document_public_id:
                try:
                    cloudinary_service.delete(obj.yellow_card_document_public_id)
                except Exception:
                    pass
            
            # Clear document fields in DB
            obj.passport_document = None
            obj.passport_document_public_id = None
            obj.yellow_card_document = None
            obj.yellow_card_document_public_id = None
            
            # Remove from completed_steps so status shows "rejected"
            obj.completed_steps.remove(step)
            
            review, _ = RegistrationStepReview.objects.get_or_create(
                registration=obj,
                step=step,
                defaults={"reviewed_by": request.user}
            )
            review.reject(request.user, reason)
            # Keep status as PENDING so user can resubmit
            obj.status = RegistrationStatus.PENDING
            obj.save()
            self._send_user_notification(obj, step.title, approved=False, rejection_reason=reason)
            self.message_user(request, f"Documents rejected: {reason}. Documents deleted. User can resubmit.", messages.WARNING)
            return super().response_change(request, obj)

        if "_reject_step2" in request.POST:
            reason = request.POST.get("reason", "").strip()
            if not reason:
                self.message_user(request, "Rejection reason is required.", messages.ERROR)
                return super().response_change(request, obj)
            
            step = obj.current_step
            
            # Remove from completed_steps so status shows "rejected"
            obj.completed_steps.remove(step)
            
            review, _ = RegistrationStepReview.objects.get_or_create(
                registration=obj,
                step=step,
                defaults={"reviewed_by": request.user}
            )
            review.reject(request.user, reason)
            # Keep status as PENDING so user can resubmit
            obj.status = RegistrationStatus.PENDING
            obj.save()
            self._send_user_notification(obj, step.title, approved=False, rejection_reason=reason)
            self.message_user(request, f"Bio-data rejected: {reason}. User can resubmit.", messages.WARNING)
            return super().response_change(request, obj)

        # Step 4 - document_review approval (if step still exists) - move to next step
        if "_approve_step3" in request.POST:
            step = RegistrationStep.objects.filter(code="document_review", is_active=True).first()
            if step:
                review, _ = RegistrationStepReview.objects.get_or_create(
                    registration=obj,
                    step=step,
                    defaults={"reviewed_by": request.user}
                )
                review.approve(request.user)
                obj.status = RegistrationStatus.PENDING
                obj.completed_steps.add(step)
                
                next_step = RegistrationStep.objects.filter(
                    order__gt=step.order,
                    is_active=True,
                ).order_by('order').first()
                
                if next_step:
                    obj.current_step = next_step
                
                obj.save()
                self._send_user_notification(obj, step.title, approved=True)
                self.message_user(request, "Documents approved! Registration moved to next step.", messages.SUCCESS)
                return super().response_change(request, obj)
            else:
                # document_review step removed, just move to next step
                next_step = RegistrationStep.objects.filter(
                    code="visa_status",
                    is_active=True
                ).first()
                if next_step:
                    obj.current_step = next_step
                obj.save()
                self.message_user(request, "Documents approved! Registration moved to next step.", messages.SUCCESS)
                return super().response_change(request, obj)

        # Step 4 - document_review rejection (if step still exists)
        if "_reject_step3" in request.POST:
            reason = request.POST.get("reason", "").strip()
            if not reason:
                self.message_user(request, "Rejection reason is required.", messages.ERROR)
                return super().response_change(request, obj)
            
            step = RegistrationStep.objects.filter(code="document_review", is_active=True).first()
            if step:
                review, _ = RegistrationStepReview.objects.get_or_create(
                    registration=obj,
                    step=step,
                    defaults={"reviewed_by": request.user}
                )
                review.reject(request.user, reason)
                # Keep status as PENDING so user can resubmit
                obj.status = RegistrationStatus.PENDING
                obj.save()
                self._send_user_notification(obj, step.title, approved=False, rejection_reason=reason)
                self.message_user(request, f"Documents rejected: {reason}. User can resubmit.", messages.WARNING)
            return super().response_change(request, obj)

        # Payment Details - Approve
        if "_approve_payment" in request.POST:
            step = RegistrationStep.objects.filter(code="payment_details").first()
            if not step:
                self.message_user(request, "Payment step not found", messages.ERROR)
                return super().response_change(request, obj)
            
            review, _ = RegistrationStepReview.objects.get_or_create(
                registration=obj,
                step=step,
                defaults={"reviewed_by": request.user}
            )
            review.approve(request.user)
            obj.status = RegistrationStatus.PENDING
            
            if not obj.completed_steps.filter(pk=step.pk).exists():
                obj.completed_steps.add(step)
            
            next_step = RegistrationStep.objects.filter(
                order__gt=step.order,
                is_active=True,
            ).order_by('order').first()
            
            if next_step:
                obj.current_step = next_step
            
            obj.save()
            self._send_user_notification(obj, step.title, approved=True)
            self.message_user(request, "Payment approved! Registration moved to next step.", messages.SUCCESS)
            return super().response_change(request, obj)

        # Payment Details - Reject
        if "_reject_payment" in request.POST:
            reason = request.POST.get("reason", "").strip()
            if not reason:
                self.message_user(request, "Rejection reason is required.", messages.ERROR)
                return super().response_change(request, obj)
            
            step = RegistrationStep.objects.filter(code="payment_details").first()
            if not step:
                self.message_user(request, "Payment step not found", messages.ERROR)
                return super().response_change(request, obj)
            
            # Remove from completed_steps so status shows "rejected"
            obj.completed_steps.remove(step)
            
            review, _ = RegistrationStepReview.objects.get_or_create(
                registration=obj,
                step=step,
                defaults={"reviewed_by": request.user}
            )
            review.reject(request.user, reason)
            # Keep status as PENDING so user can resubmit
            obj.status = RegistrationStatus.PENDING
            obj.save()
            self._send_user_notification(obj, step.title, approved=False, rejection_reason=reason)
            self.message_user(request, f"Payment rejected: {reason}. User can resubmit.", messages.WARNING)
            return super().response_change(request, obj)

        return super().response_change(request, obj)

    # -----------------------------
    # Read-only display methods
    # -----------------------------
    def get_visa_status_display(self, obj):
        if obj.visa_status:
            status_colors = {
                "pending": "🟡 Pending",
                "ready": "🟢 Ready", 
                "issued": "🔵 Issued",
                "rejected": "🔴 Rejected"
            }
            return status_colors.get(obj.visa_status, obj.visa_status)
        return "Pending"
    get_visa_status_display.short_description = "Visa Status"

    def get_journey_status_display(self, obj):
        if obj.journey_presence_status:
            status_colors = {
                "pre_travel": "🟡 Awaiting Travel",
                "in_mecca": "🟢 In Destination",
                "arrived": "🔵 Arrived",
                "did_not_arrive": "🔴 Did Not Arrive"
            }
            return status_colors.get(obj.journey_presence_status, obj.journey_presence_status)
        return "Awaiting Travel"
    get_journey_status_display.short_description = "Journey Status"

    def get_account_summary(self, obj):
        u = obj.user
        return format_html(
            "User: {} | Email: {} | Phone: {}",
            u.username or "-",
            u.email or "-",
            u.phone or "-"
        )
    get_account_summary.short_description = "Account Info"

    # -----------------------------
    # Document previews
    # -----------------------------
    def get_passport_preview(self, obj):
        pic = obj.passport_document
        # Must be valid Cloudinary URL
        if pic and (pic.startswith('http://') or pic.startswith('https://')):
            return format_html(
                '<a href="{0}" target="_blank" class="button" style="background:#447e9b; color:white; padding:4px 8px;">Open Passport</a>',
                pic
            )
        return "Not uploaded"

    def get_yellow_card_preview(self, obj):
        pic = obj.yellow_card_document
        # Must be valid Cloudinary URL
        if pic and (pic.startswith('http://') or pic.startswith('https://')):
            return format_html(
                '<a href="{0}" target="_blank" class="button" style="background:#447e9b; color:white; padding:4px 8px;">Open Yellow Card</a>',
                pic
            )
        return "Not uploaded"

    def get_travel_documents_list(self, obj):
        docs = obj.travel_documents.all()
        if not docs.exists():
            return "No travel documents uploaded"
        
        html = "<ul style='list-style:none; padding-left:0;'>"
        for doc in docs:
            html += f"<li style='margin-bottom:8px;'>"
            html += f"<b>{doc.get_doc_type_display()}:</b> {doc.title}<br>"
            html += f"<a href='{doc.file.url}' target='_blank' style='background:#447e9b; color:white; padding:2px 6px; font-size:12px;'>Open</a>"
            html += f"</li>"
        html += "</ul>"
        return format_html(html)

    # -----------------------------
    # List Display Helpers
    # -----------------------------
    def get_user_display(self, obj):
        u = obj.user
        return u.username or u.email or u.phone
    get_user_display.short_description = "User"

    def get_current_step_display(self, obj):
        return obj.current_step.title if obj.current_step else "N/A"

    # Disable add
    def has_add_permission(self, request): return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.journey_presence_status in [JourneyPresenceStatus.ARRIVED, JourneyPresenceStatus.IN_MECCA]:
            return False
        return True


# -----------------------------
# SupportTicketReply Inline
# -----------------------------
class SupportTicketReplyInline(admin.TabularInline):
    model = SupportTicketReply
    extra = 0
    readonly_fields = ("user", "message", "created_at", "is_internal")
    can_delete = False
    fields = ("user", "message", "created_at", "is_internal")

    def has_view_permission(self, request, obj=None): return True
    def has_add_permission(self, request, obj=None): return True


# -----------------------------
# SupportTicketAdmin
# -----------------------------
@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "get_user_display", "subject", "category", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("subject", "user__username", "user__email", "user__phone")
    readonly_fields = ("user", "registration", "category", "subject", "message", "created_at", "updated_at")
    inlines = [SupportTicketReplyInline]
    change_form_template = "admin/supportticket_change_form.html"

    def get_user_display(self, obj):
        u = obj.user
        return u.username or u.email or u.phone
    get_user_display.short_description = "User"

    def has_add_permission(self, request): return False


# -----------------------------
# ManasikGuidance Admin
# -----------------------------
@admin.register(ManasikGuidance)
class ManasikGuidanceAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "guidance_type", "order", "is_active")
    list_filter = ("guidance_type", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "content")


# -----------------------------
# EmergencyContact Admin
# -----------------------------
@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "contact_type", "value", "is_active", "order")
    list_filter = ("contact_type", "is_active")
    list_editable = ("is_active", "order")
    search_fields = ("name", "value")
