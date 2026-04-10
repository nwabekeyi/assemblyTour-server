# newsletter/urls.py
from django.urls import path
from .views import (
    NewsletterRequestCreateView,
    NewsletterListView,
    NewsletterSendView,
    SubscriberListView
)

urlpatterns = [
    path("newsletter/subscribe/", NewsletterRequestCreateView.as_view(), name="newsletter-subscribe"),
    path("newsletter/", NewsletterListView.as_view(), name="newsletter-list"),
    path("newsletter/send/", NewsletterSendView.as_view(), name="newsletter-send"),
    path("newsletter/subscribers/", SubscriberListView.as_view(), name="newsletter-subscribers"),
]