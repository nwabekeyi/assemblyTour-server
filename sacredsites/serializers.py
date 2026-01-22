from rest_framework import serializers
from .models import SacredSite


class SacredSiteSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = SacredSite
        fields = [
            "id",
            "name",
            "description",
            "image",
            "is_active",
        ]

    def get_image(self, obj):
        return obj.image.url if obj.image else None
