from django.contrib import admin
from django.core.exceptions import ValidationError, PermissionDenied
from .models import RegistrationStep, HajjRegistration


@admin.register(RegistrationStep)
class RegistrationStepAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "code",
        "title",
        "action_type",
        "data_scope",
        "is_active",
    )

    list_display_links = ("code",)
    list_editable = ("order", "is_active")
    search_fields = ("code", "title", "data_scope")
    ordering = ("order",)

    fieldsets = (
        ("Step Details", {
            "fields": (
                "code",
                "title",
                "description",
                "order",
                "is_active",
            )
        }),
        ("Step Configuration", {
            "fields": (
                "action_type",
                "data_scope",
            ),
            "description": (
                "Defines what this step does and "
                "which part of the database it updates."
            ),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Make the first step read-only
        """
        if obj and obj.order == 1:
            # All fields become readonly for the first step
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of the first step
        """
        if obj and obj.order == 1:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # Prevent editing the first step
        if change and obj.order == 1:
            raise PermissionDenied("The first registration step cannot be edited.")

        # Keep existing validation for duplicate data_scope
        if not change and RegistrationStep.objects.filter(
            data_scope=obj.data_scope
        ).exists():
            raise ValidationError(
                f"A step with data scope '{obj.data_scope}' already exists."
            )

        super().save_model(request, obj, form, change)


@admin.register(HajjRegistration)
class HajjRegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "current_step", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("completed_steps",)

    actions = ["move_to_next_step", "move_to_previous_step"]

    def move_to_next_step(self, request, queryset):
        steps = list(
            RegistrationStep.objects.filter(is_active=True).order_by("order")
        )

        for reg in queryset:
            if reg.current_step not in steps:
                continue

            index = steps.index(reg.current_step)
            if index + 1 < len(steps):
                reg.completed_steps.add(reg.current_step)
                reg.current_step = steps[index + 1]
                reg.save(update_fields=["current_step"])

    def move_to_previous_step(self, request, queryset):
        steps = list(
            RegistrationStep.objects.filter(is_active=True).order_by("order")
        )

        for reg in queryset:
            if reg.current_step not in steps:
                continue

            index = steps.index(reg.current_step)
            if index > 0:
                reg.completed_steps.remove(reg.current_step)
                reg.current_step = steps[index - 1]
                reg.save(update_fields=["current_step"])
