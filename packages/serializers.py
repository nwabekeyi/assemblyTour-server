from rest_framework import serializers
from .models import Package


class PackageSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "location",
            "cover_image",
            "cover_image_url",
            "price_current",
            "price_original",
            "description",
            "spiritual_highlights",
            "duration_days",
            "duration_nights",
            "group_size_min",
            "group_size_max",
            "created_at",
        ]
        read_only_fields = ["created_at", "cover_image_url"]

    def get_cover_image_url(self, obj):
        """
        Safely expose Cloudinary URL
        """
        if obj.cover_image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None
