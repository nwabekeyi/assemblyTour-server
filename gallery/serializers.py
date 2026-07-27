from rest_framework import serializers
from .models import Gallery


class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = [
            "id",
            "title",
            "slug",
            "media_type",
            "url",
            "thumbnail_url",
            "description",
            "display_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]
