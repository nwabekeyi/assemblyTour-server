# newsletter/views.py
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from .models import NewsletterRequest
from .serializers import NewsletterRequestSerializer
from core.utils.api_response import api_response

class NewsletterRequestCreateView(generics.CreateAPIView):
    queryset = NewsletterRequest.objects.all()
    serializer_class = NewsletterRequestSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(
                data=serializer.data,
                message="Thank you for subscribing!",
                success=True,
                status_code=status.HTTP_201_CREATED
            )
        return api_response(
            errors=serializer.errors,
            message="Subscription failed",
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST
        )
