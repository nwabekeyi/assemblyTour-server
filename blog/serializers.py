from rest_framework import serializers
from .models import BlogPost, BlogComment
from django.contrib.auth import get_user_model

User = get_user_model()


# --------------------------
# LIST SERIALIZER
# --------------------------
class BlogPostListSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    author_image_url = serializers.SerializerMethodField()
    # read_time is now editable by admin and returned as-is
    read_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "author_name",
            "author_image_url",
            "published_at",
            "views_count",
            "likes_count",
            "cover_image_url",
            "read_time",
        ]

    def get_cover_image_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def get_author_image_url(self, obj):
        request = self.context.get("request")
        if obj.author_image and request:
            return request.build_absolute_uri(obj.author_image.url)
        return None


class BlogPostDetailSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    author_image_url = serializers.SerializerMethodField()
    read_time = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "content",
            "author_name",
            "author_image_url",
            "published_at",
            "views_count",
            "likes_count",
            "read_time",
            "comments_count",
            "cover_image_url",
        ]

    def get_cover_image_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def get_author_image_url(self, obj):
        request = self.context.get("request")
        if obj.author_image and request:
            return request.build_absolute_uri(obj.author_image.url)
        return None


# --------------------------
# COMMENT SERIALIZER
# --------------------------
class BlogCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = [
            "id",
            "content",
            "user_name",
            "created_at",
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


