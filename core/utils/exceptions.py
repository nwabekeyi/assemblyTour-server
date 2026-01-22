from rest_framework import permissions
from rest_framework.views import APIView
from core.utils.api_response import api_response
from .models import HeroSlide, ExperienceSection
from .serializers import HeroSlideSerializer, ExperienceSectionSerializer

class HomeContentView(APIView):
    """
    Home page content API (public for users).
    Only GET is exposed.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Only active content
        hero_slides = HeroSlide.objects.filter(is_active=True)
        experience_sections = ExperienceSection.objects.filter(is_active=True)

        hero_serializer = HeroSlideSerializer(hero_slides, many=True)
        exp_serializer = ExperienceSectionSerializer(experience_sections, many=True)

        data = {
            "hero_slides": hero_serializer.data,
            "experience_sections": exp_serializer.data
        }
        return api_response(data=data, message="Home content retrieved successfully.")
