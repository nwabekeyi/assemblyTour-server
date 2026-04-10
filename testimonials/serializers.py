from rest_framework import serializers
from .models import Testimonial


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'author_name', 'author_image', 'content', 'is_active', 'created_at']