from rest_framework import generics, permissions
from core.utils.api_response import api_response
from .models import FAQ
from .serializers import FAQSerializer

class FAQListView(generics.ListAPIView):
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        faqs = self.get_queryset()
        serializer = self.get_serializer(faqs, many=True)
        return api_response(
            success=True,
            message="FAQs fetched successfully",
            data=serializer.data,
            errors=None,
            status_code=200
        )

class FAQDetailView(generics.RetrieveAPIView):
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    lookup_field = "id"
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        faq = self.get_object()
        serializer = self.get_serializer(faq)
        return api_response(
            success=True,
            message="FAQ fetched successfully",
            data=serializer.data,
            errors=None,
            status_code=200
        )
