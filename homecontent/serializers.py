from rest_framework import serializers
from .models import HeroSlide, ExperienceSection

class HeroSlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSlide
        fields = ["id", "title", "body", "image", "order"]


class ExperienceSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperienceSection
        fields = ["id", "title", "body", "image_one", "image_two"]
