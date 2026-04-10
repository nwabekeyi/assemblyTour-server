from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Testimonial
from .serializers import TestimonialSerializer
from core.utils.api_response import api_response


class TestimonialListView(generics.ListAPIView):
    serializer_class = TestimonialSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Testimonial.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        if not queryset.exists():
            # Return placeholder data if no testimonials exist
            placeholder_data = [
                {
                    "id": 1,
                    "author_name": "Ahmed Al-Mansour",
                    "author_image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
                    "content": "Alhamdulillah, the Umrah journey was perfectly organized. The guides were knowledgeable, the hotels were close to the Haram, and everything ran smoothly. May Allah reward the team abundantly!",
                    "is_active": True,
                    "created_at": None
                },
                {
                    "id": 2,
                    "author_name": "Fatima Rahman",
                    "author_image": "https://images.unsplash.com/photo-1589571894960-20bbe2828d0a?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
                    "content": "This was my first Umrah, and I felt completely at ease. The team took care of every detail, from visa to ziyarah in Madinah. Truly a blessed and peaceful experience. JazakAllah khairan!",
                    "is_active": True,
                    "created_at": None
                },
                {
                    "id": 3,
                    "author_name": "Khalid bin Walid",
                    "author_image": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
                    "content": "Excellent service throughout our Hajj package. The accommodation, transport, and scholarly guidance during the rites were outstanding. Highly recommended for anyone planning their pilgrimage.",
                    "is_active": True,
                    "created_at": None
                },
                {
                    "id": 4,
                    "author_name": "Aisha Siddiqua",
                    "author_image": "https://images.unsplash.com/photo-1554151228-14d9def656e4?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
                    "content": "MashaAllah, what a beautiful spiritual journey! The extended stay in Madinah allowed us to pray in Rawdah and visit all the holy sites with ease. The team's care and devotion made it unforgettable.",
                    "is_active": True,
                    "created_at": None
                },
            ]
            return api_response(
                success=True,
                message="Using placeholder testimonials",
                data=placeholder_data,
                errors=None,
                status_code=200
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            success=True,
            message="Testimonials fetched successfully",
            data=serializer.data,
            errors=None,
            status_code=200
        )