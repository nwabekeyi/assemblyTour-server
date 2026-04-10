# newsletter/serializers.py
from rest_framework import serializers
from .models import NewsletterRequest, Newsletter

class NewsletterRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterRequest
        fields = ["id", "email", "created_at"]


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = ["id", "subject", "message", "sent_at", "created_by", "created_at"]