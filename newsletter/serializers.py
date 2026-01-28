# newsletter/serializers.py
from rest_framework import serializers
from .models import NewsletterRequest

class NewsletterRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterRequest
        fields = ["id", "email", "created_at"]
