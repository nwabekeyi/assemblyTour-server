from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from core.utils.api_response import api_response
from .models import ContactMessage
from .serializers import ContactMessageSerializer


class ContactMessageCreateView(generics.CreateAPIView):
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        name = request.data.get("name", "").strip()
        email = request.data.get("email", "").strip()
        subject = request.data.get("subject", "").strip()
        message = request.data.get("message", "").strip()

        if not name:
            return api_response(message="Name is required", status_code=400)
        if not email:
            return api_response(message="Email is required", status_code=400)
        if not subject:
            return api_response(message="Subject is required", status_code=400)
        if not message:
            return api_response(message="Message is required", status_code=400)

        try:
            validate_email(email)
        except ValidationError:
            return api_response(message="Invalid email address", status_code=400)

        contact = ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        serializer = self.get_serializer(contact)
        return api_response(data=serializer.data, message="Message sent successfully", status_code=201)