from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from core.utils.api_response import api_response


@method_decorator(
    ratelimit(key="ip", rate="30/m", block=True),
    name="dispatch"
)
class LivenessView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return api_response(
            success=True,
            message="Service is alive",
            data={
                "status": "ok"
            },
            errors=None,
            status_code=status.HTTP_200_OK
        )
