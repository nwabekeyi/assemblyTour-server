# newsletter/urls.py
from django.urls import path
from .views import NewsletterRequestCreateView

urlpatterns = [
    path("newsletter/subscribe/", NewsletterRequestCreateView.as_view(), name="newsletter-subscribe"),
]
