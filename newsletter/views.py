# newsletter/views.py
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import NewsletterRequest, Newsletter
from .serializers import NewsletterRequestSerializer, NewsletterSerializer
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


class NewsletterListView(generics.ListAPIView):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None


class NewsletterSendView(generics.CreateAPIView):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        subject = request.data.get('subject')
        message = request.data.get('message')

        if not subject or not message:
            return api_response(
                errors={'detail': 'Subject and message are required'},
                message="Failed to send newsletter",
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Get all subscribed emails
        subscribers = NewsletterRequest.objects.values_list('email', flat=True)
        
        if not subscribers:
            return api_response(
                errors={'detail': 'No subscribers found'},
                message="No subscribers to send to",
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Create newsletter record
        newsletter = Newsletter.objects.create(
            subject=subject,
            message=message,
            created_by=request.user if request.user.is_authenticated else None,
            sent_at=timezone.now()
        )

        # Send email to all subscribers
        try:
            send_mail(
                subject=f"[Assembly Tours] {subject}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(subscribers),
                fail_silently=False,
            )
            return api_response(
                data={'id': newsletter.id, 'subject': subject, 'recipients': len(subscribers)},
                message=f"Newsletter sent to {len(subscribers)} subscribers",
                success=True,
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            newsletter.sent_at = None
            newsletter.save()
            return api_response(
                errors={'detail': str(e)},
                message="Failed to send newsletter",
                success=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriberListView(generics.ListAPIView):
    queryset = NewsletterRequest.objects.all()
    serializer_class = NewsletterRequestSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None