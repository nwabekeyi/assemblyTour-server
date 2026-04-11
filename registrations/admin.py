from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.files.storage import default_storage
from django.utils import timezone
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from .models import (
    RegistrationStep,
    RegistrationStatus,
    VisaStatus,
    JourneyPresenceStatus,
    HajjRegistration,
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


class HajjRegistrationAdminForm(forms.ModelForm):
    class Meta:
        model = HajjRegistration
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
class TravelDocumentInline(admin.StackedInline):
    model = TravelDocument
    extra = 0
    max_num = 3
    readonly_fields = ("uploaded_by", "uploaded_at")
    fields = ("doc_type", "title", "file", "description", "uploaded_by", "uploaded_at")

    def has_delete_permission(self, request, obj=None): return True
    def has_add_permission(self, request, obj=None): return True

    def get_extra(self, request, obj=None):
        if obj and obj.travel_documents.exists():
            existing_count = obj.travel_documents.count()
            return max(0, 3 - existing_count)
        return 1

    def formfield_for_dbfsfsfsfsf(self, db_field, request, **kwargs):
        if db_field.name == "doc_type":
            kwargs["queryset"] = TravelDocumentType.objects.filter(
                value__in=["visa", "ticket", "hotel_voucher"]
            )
        return super(TravelDocumentInline, self).formfield_for_dbfsfsfsfsf(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        
        existing = obj.registration.travel_documents.filter(doc_type=obj.doc_type).first()
        if existing:
            if obj.pk:
                obj.pk = existing.pk
            else:
                from django.core.exceptions import ValidationError
                raise ValidationError(f"A {obj.get_doc_type_display()} document already exists for this registration.")
        
        super(TravelDocumentInline, self).save_model(request, obj, form, change)
        
        complete_travel_documents_step(obj.registration)


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
class TravelDocumentInline(admin.StackedInline):
    model = TravelDocument
    extra = 0
    max_num = 3
    readonly_fields = ("uploaded_by", "uploaded_at")
    fields = ("doc_type", "title", "file", "description", "uploaded_by", "uploaded_at")

    def has_delete_permission(self, request, obj=None): return True
    def has_add_permission(self, request, obj=None): return True

    def get_extra(self, request, obj=None):
        if obj and obj.travel_documents.exists():
            existing_count = obj.travel_documents.count()
            return max(0, 3 - existing_count)
        return 1

    def formfield_for_dbfsfsfsfsfsf(self, db_field, request, **kwargs):
        if db_field.name == "doc_type" and request and hasattr(request, 'self') and hasattr(request.self, 'parent_instance'):
            reg = request.self.parent_instance
            used_types = list(reg.travel_documents.values_list('doc_type', flat=True))
            kwargs["queryset"] = TravelDocumentType.objects.filter(
                value__in=["visa", "ticket", "hotel_voucher"]
            ).exclude(value__in=used_types)
        return super(TravelDocumentInline, self).formfield_for_dbfsfsfsfsf(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        
        existing = obj.registration.travel_documents.filter(doc_type=obj.doc_type).first()
        if existing:
            if obj.pk:
                obj.pk = existing.pk
            else:
                from django.core.exceptions import ValidationError
                raise ValidationError(f"A {obj.get_doc_type_display()} document already exists for this registration.")
        
        super(TravelDocumentInline, self).save_model(request, obj, form, change)
        
        complete_travel_documents_step(obj.registration)


# -----------------------------
# RegistrationStepReview Inline
# -----------------------------
class RegistrationStepReviewInline(admin.TabularInline):
    model = RegistrationStepReview
    extra = 0
    readonly_fields = ("step", "status", "rejection_reason", "reviewed_by", "reviewed_at")
    can_delete = False

    def has_view_permission(self, request, obj=None): return True
    def has_add_permission(self, request, obj=None): return False


# -----------------------------
# HajjRegistrationAdmin
# -----------------------------
@admin.register(HajjRegistration)
class HajjRegistrationAdmin(admin.ModelAdmin):
    form = HajjRegistrationAdminForm
    list_display = ("get_user_display", "get_current_step_display", "status", "visa_status", "updated_at")
    list_filter = ("status", "visa_status", "current_step")
    search_fields = ("user__username", "user__email", "user__phone")
    inlines = [TravelDocumentInline]
    readonly_fields = (
        "user", "package", "current_step", "status", "completed_steps",
        "get_user_bio_summary", "get_passport_preview", "get_yellow_card_preview",
        "get_travel_documents_list", "get_payment_proof_preview", "get_payment_review_status",
        "created_at", "updated_at"
    )

    change_form_template = "admin/hajjregistration_change_form.html"

    # -----------------------------
    # Fieldsets
    # -----------------------------
    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ("Core Progress", {"fields": ("user", "package", "current_step", "status", "visa_status", "journey_presence_status", "completed_steps")}),
        ]

        if obj:
            # Step 2: In progress
            if obj.current_step.code == "registration_form":
                fieldsets.append(("Step 2: User Bio", {
                    "fields": ("get_user_bio_summary",),
                    "description": "Step in progress. Approve or Reject below."
                }))
            # Step 2: Approved
            elif obj.completed_steps.filter(code="registration_form").exists():
                fieldsets.append(("Step 2: Approved Bio-Data", {
                    "fields": ("get_user_bio_summary",),
                }))

            # Step 3 Documents
            if obj.completed_steps.filter(code="document_upload").exists():
                fieldsets.append(("Step 3: User Documents", {
                    "fields": ("get_passport_preview", "get_yellow_card_preview"),
                    "description": "Documents uploaded. Approve or Reject below."
                }))
            
            # Step 4: Document Review
            if obj.current_step.code == "document_review":
                review = obj.step_reviews.filter(step__code="document_review").first()
                if review:
                    if review.status == "pending":
                        fieldsets.append(("Step 4: Document Review", {
                            "fields": ("get_passport_preview", "get_yellow_card_preview"),
                            "description": "Documents awaiting review. Approve or Reject below."
                        }))
                    elif review.status == "approved":
                        fieldsets.append(("Step 4: Document Review Approved", {
                            "fields": ("get_passport_preview", "get_yellow_card_preview"),
                        }))

            # Step 4.5: Payment Details
            payment_step = RegistrationStep.objects.filter(code="payment_details").first()
            if payment_step:
                payment_review = obj.step_reviews.filter(step=payment_step).first()
                payment_uploaded = obj.payment_details.exists()
                
                if payment_uploaded:
                    if not payment_review or payment_review.status == "pending":
                        fieldsets.append(("Step 4.5: Payment Details", {
                            "fields": ("get_payment_proof_preview", "get_payment_review_status"),
                            "description": "Payment proof uploaded. Approve or Reject below."
                        }))
                    elif payment_review.status == "approved":
                        fieldsets.append(("Step 4.5: Payment Approved", {
                            "fields": ("get_payment_proof_preview",),
                        }))

            # Step 5: Visa Status
            fieldsets.append(("Step 5: Visa Status", {
                "fields": ("visa_status", "visa_status_notes"),
                "description": "Set whether the visa is pending, ready, or failed."
            }))

            # Step 6: Travel Documents
            fieldsets.append(("Step 6: Travel Documents", {
                "fields": ("get_travel_documents_list",),
                "description": "Review or upload travel documents such as visas, tickets, and hotel vouchers using the inline section below."
            }))

            # Step 7: Arrival Status (final step)
            fieldsets.append(("Step 7: Arrival Status", {
                "fields": ("journey_presence_status", "journey_presence_notes"),
                "description": "Default state is 'Awaiting Travel'. Update when the pilgrim departs, arrives, or if an incident occurs."
            }))

            # System metadata
            fieldsets.append(("System Metadata", {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",)
            }))

        return fieldsets

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and obj.journey_presence_status == JourneyPresenceStatus.ARRIVED:
            extra_context = extra_context or {}
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False
            extra_context['show_save_as_new'] = False
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if change and obj.journey_presence_status == JourneyPresenceStatus.ARRIVED:
            return
        super().save_model(request, obj, form, change)
        self._handle_visa_status_transition(request, obj)
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

    def _handle_journey_presence_transition(self, request, obj):
        if not obj:
            return

        step = RegistrationStep.objects.filter(code="arrival_status").first()
        state = obj.journey_presence_status

        if state == JourneyPresenceStatus.IN_MECCA:
            if obj.status == RegistrationStatus.NOT_STARTED:
                obj.status = RegistrationStatus.PENDING
                obj.save(update_fields=["status", "updated_at"])
                self.message_user(
                    request,
                    "Pilgrim marked as currently in Mecca.",
                    messages.SUCCESS
                )
        elif state == JourneyPresenceStatus.ARRIVED:
            if step and not obj.completed_steps.filter(pk=step.pk).exists():
                obj.completed_steps.add(step)
            obj.status = RegistrationStatus.COMPLETED
            obj.save(update_fields=["status", "updated_at"])
            self.message_user(
                request,
                "Pilgrim marked as arrived and registration completed.",
                messages.SUCCESS
            )
        elif state == JourneyPresenceStatus.DID_NOT_ARRIVE:
            if step and not obj.completed_steps.filter(pk=step.pk).exists():
                obj.completed_steps.add(step)
            obj.status = RegistrationStatus.FAILED
            obj.save(update_fields=["status", "updated_at"])
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
        
        bio_html = format_html(
            "<b>Name:</b> {}<br>"
            "<b>Phone:</b> {}<br>"
            "<b>Email:</b> {}<br>"
            "<b>Passport #:</b> {}<br>"
            "<b>DOB:</b> {}<br>"
            "<b>Address:</b> {}",
            name,
            u.phone,
            u.email or "-",
            u.passport_number or "-",
            u.date_of_birth or "-",
            u.address or "-"
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
            ).exclude(code="payment_review").order_by('order').first()
            
            if next_step:
                obj.current_step = next_step
            
            obj.save()
            self._send_user_notification(obj, step.title, approved=True)
            self.message_user(request, "Bio-data approved! User moved to document upload step.", messages.SUCCESS)
            return super().response_change(request, obj)

        if "_reject_step2" in request.POST:
            reason = request.POST.get("reason", "").strip()
            if not reason:
                self.message_user(request, "Rejection reason is required.", messages.ERROR)
            else:
                step = obj.current_step
                review, _ = RegistrationStepReview.objects.get_or_create(
                    registration=obj,
                    step=step,
                    defaults={"reviewed_by": request.user}
                )
                review.reject(request.user, reason)
                obj.status = RegistrationStatus.FAILED
                obj.save()
                self._send_user_notification(obj, step.title, approved=False, rejection_reason=reason)
                self.message_user(request, f"Bio-data rejected: {reason}", messages.WARNING)
            return super().response_change(request, obj)

        # Step 4 - document_review approval - move to next step
        if "_approve_step3" in request.POST:
            step = RegistrationStep.objects.filter(code="document_review").first()
            if not step:
                self.message_user(request, "Document review step not found", messages.ERROR)
                return super().response_change(request, obj)
            
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
            ).exclude(code="payment_review").order_by('order').first()
            
            if next_step:
                obj.current_step = next_step
            
            obj.save()
            self._send_user_notification(obj, step.title, approved=True)
            self.message_user(request, "Documents approved! Registration moved to next step.", messages.SUCCESS)
            return super().response_change(request, obj)

        # Step 4 - document_review rejection
        if "_reject_step3" in request.POST:
            reason = request.POST.get("reason", "").strip()
            if not reason:
                self.message_user(request, "Rejection reason is required.", messages.ERROR)
                return super().response_change(request, obj)
            
            step = RegistrationStep.objects.filter(code="document_review").first()
            if step:
                review, _ = RegistrationStepReview.objects.get_or_create(
                    registration=obj,
                    step=step,
                    defaults={"reviewed_by": request.user}
                )
                review.reject(request.user, reason)
                obj.status = RegistrationStatus.FAILED
                obj.save()
                self._send_user_notification(obj, step.title, approved=False, rejection_reason=reason)
                self.message_user(request, f"Documents rejected: {reason}", messages.WARNING)
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
            ).exclude(code="payment_review").order_by('order').first()
            
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
            if step:
                review, _ = RegistrationStepReview.objects.get_or_create(
                    registration=obj,
                    step=step,
                    defaults={"reviewed_by": request.user}
                )
                review.reject(request.user, reason)
                obj.status = RegistrationStatus.FAILED
                obj.save()
                self._send_user_notification(obj, step.title, approved=False, rejection_reason=reason)
                self.message_user(request, f"Payment rejected: {reason}", messages.WARNING)
            return super().response_change(request, obj)

        return super().response_change(request, obj)

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

    # Disable add/delete
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False


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
