from rest_framework import serializers
from .models import RegistrationStep, HajjRegistration

class RegistrationStepSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = RegistrationStep
        fields = (
            "code",
            "title",
            "description",
            "action_type",
            "data_scope",
            "order",
            "is_completed",
            "is_current",
        )

    def get_is_completed(self, step):
        registration = self.context.get("registration")
        if not registration:
            return False
        return registration.completed_steps.filter(id=step.id).exists()

    def get_is_current(self, step):
        registration = self.context.get("registration")
        if not registration:
            return False
        return registration.current_step_id == step.id

class UserRegistrationProgressSerializer(serializers.ModelSerializer):
    current_step = RegistrationStepSerializer(read_only=True)
    completed_steps = RegistrationStepSerializer(many=True, read_only=True)

    class Meta:
        model = HajjRegistration
        fields = (
            "current_step",
            "completed_steps",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["meta"] = {
            "current_step_order": instance.current_step.order,
            "completed_steps_count": instance.completed_steps.count(),
            "is_completed": instance.completed_steps.filter(
                id=instance.current_step_id
            ).exists(),
        }

        return data

