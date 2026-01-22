from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core.utils.api_response import api_response
from .models import HeroSlide, ExperienceSection
from .serializers import HeroSlideSerializer, ExperienceSectionSerializer

class HomeContentView(APIView):
    """
    Public endpoint to fetch homepage content
    """
    permission_classes = [AllowAny]

    def get(self, request):
        hero_slides = HeroSlide.objects.filter(is_active=True)
        experience = ExperienceSection.objects.filter(is_active=True).first()

        data = {
            "hero_slides": HeroSlideSerializer(hero_slides, many=True).data,
            "experience_section": (
                ExperienceSectionSerializer(experience).data if experience else None
            ),
        }

        return api_response(
            data=data,
            message="Home content fetched successfully"
        )
