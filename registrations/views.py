from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import RegistrationStep, HajjRegistration
from .serializers import UserRegistrationProgressSerializer
from core.utils.api_response import api_response


class UserRegistrationStepsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        steps = RegistrationStep.objects.filter(is_active=True).order_by("order")

        if not steps.exists():
            return api_response(
                success=False,
                message="Registration steps are not configured",
                data=None,
                errors={"steps": "No active registration steps found"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        registration, created = HajjRegistration.objects.get_or_create(
            user=request.user,
            defaults={"current_step": steps.first()},
        )

        serializer = UserRegistrationProgressSerializer(registration)

        return api_response(
            success=True,
            message="Registration steps retrieved successfully",
            data={
                "current_step": {
                    "code": registration.current_step.code,
                    "title": registration.current_step.title,
                    "description": registration.current_step.description,
                    "action_type": registration.current_step.action_type,
                    "data_scope": registration.current_step.data_scope,
                    "order": registration.current_step.order,
                },
                "all_steps": [
                    {
                        "code": step.code,
                        "title": step.title,
                        "description": step.description,
                        "action_type": step.action_type,
                        "data_scope": step.data_scope,
                        "order": step.order,
                        "is_completed": step in registration.completed_steps.all(),
                        "is_current": step == registration.current_step,
                    }
                    for step in steps
                ],
                "progress": serializer.data,
            },
            errors=None,
            status_code=status.HTTP_200_OK,
        )
