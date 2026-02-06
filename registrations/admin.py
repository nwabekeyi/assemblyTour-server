from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from .models import RegistrationStep, HajjRegistration, RegistrationStepReview

# -----------------------------
# RegistrationStepAdmin
# -----------------------------
@admin.register(RegistrationStep)
class RegistrationStepAdmin(admin.ModelAdmin):
    list_display = ("order", "code", "title", "action_type", "data_scope", "is_active")
    readonly_fields = [f.name for f in RegistrationStep._meta.fields]

    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False


# -----------------------------
# HajjRegistrationAdmin
# -----------------------------
@admin.register(HajjRegistration)
class HajjRegistrationAdmin(admin.ModelAdmin):
    list_display = ("get_user_display", "get_current_step_display", "status", "updated_at")
    list_filter = ("status", "current_step")
    readonly_fields = (
        "user", "package", "current_step", "status", "completed_steps",
        "get_user_bio_summary", "get_passport_preview", "get_yellow_card_preview",
        "created_at", "updated_at"
    )

    change_form_template = "admin/hajjregistration_change_form.html"

    # -----------------------------
    # Fieldsets
    # -----------------------------
    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ("Core Progress", {"fields": ("user", "package", "current_step", "status", "completed_steps")}),
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
                fieldsets.append(("Step 3: Approved User Documents", {
                    "fields": ("get_passport_preview", "get_yellow_card_preview"),
                }))

            # Step 6 & 7: Journey
            fieldsets.append(("Step 6 & 7: Journey & Travel Details", {
                "fields": ("ticket_info", "hotel_info", "package_benefits"),
                "description": "Admin: Fill this once travel documents are ready."
            }))

            # System metadata
            fieldsets.append(("System Metadata", {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",)
            }))

        return fieldsets

    # -----------------------------
    # User Bio Display
    # -----------------------------
    def get_user_bio_summary(self, obj):
        u = obj.user
        name = " ".join(filter(None, [u.first_name, u.last_name])) or u.username or u.email or u.phone
        return format_html(
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
    get_user_bio_summary.short_description = "User Bio"

    # -----------------------------
    # Approve / Reject Step 2
    # -----------------------------
    def response_change(self, request, obj):
        if "_approve_step2" in request.POST:
            review, _ = RegistrationStepReview.objects.get_or_create(
                registration=obj,
                step=obj.current_step,
                defaults={"reviewed_by": request.user}
            )
            review.approve(request.user)
            obj.status = "completed"
            obj.save()
            self.message_user(request, "Step 2 approved successfully!", messages.SUCCESS)
            return super().response_change(request, obj)

        if "_reject_step2" in request.POST:
            reason = request.POST.get("reason", "").strip()
            if not reason:
                self.message_user(request, "Rejection reason is required.", messages.ERROR)
            else:
                review, _ = RegistrationStepReview.objects.get_or_create(
                    registration=obj,
                    step=obj.current_step,
                    defaults={"reviewed_by": request.user}
                )
                review.reject(request.user, reason)
                obj.status = "failed"
                obj.save()
                self.message_user(request, f"Step 2 rejected with reason: {reason}", messages.WARNING)
            return super().response_change(request, obj)

        return super().response_change(request, obj)

    # -----------------------------
    # Document previews
    # -----------------------------
    def get_passport_preview(self, obj):
        if obj.passport_document:
            return format_html(
                '<a href="{0}" target="_blank" class="button" style="background:#447e9b; color:white; padding:4px 8px;">Open Passport</a>',
                obj.passport_document.url
            )
        return "Not available"

    def get_yellow_card_preview(self, obj):
        if obj.yellow_card_document:
            return format_html(
                '<a href="{0}" target="_blank" class="button" style="background:#447e9b; color:white; padding:4px 8px;">Open Yellow Card</a>',
                obj.yellow_card_document.url
            )
        return "Not available"

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
