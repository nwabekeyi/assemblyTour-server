from rest_framework import serializers
from .models import Gallery


class GallerySerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = Gallery
        fields = [
            "id",
            "title",
            "slug",
            "media_type",
            "url",
            "thumbnail_url",
            "media_url",
            "description",
            "display_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        if obj.thumbnail and not request:
            return obj.thumbnail.url
        return None

    def get_media_url(self, obj):
        request = self.context.get("request")
        if obj.media and request:
            return request.build_absolute_uri(obj.media.url)
        if obj.media and not request:
            return obj.media.url
        return None
