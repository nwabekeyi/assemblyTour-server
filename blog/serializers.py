from rest_framework import serializers
from .models import BlogPost, BlogComment
from django.contrib.auth import get_user_model

User = get_user_model()


# --------------------------
# LIST SERIALIZER
# --------------------------
class BlogPostListSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "author_email",
            "published_at",
            "views_count",
            "likes_count",
            "cover_image_url",
        ]

    def get_cover_image_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
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
        return obj.user.email

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# --------------------------
# BLOG DETAIL SERIALIZER
# --------------------------
class BlogPostDetailSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)
    comments = BlogCommentSerializer(many=True, read_only=True)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "content",
            "author_email",
            "published_at",
            "views_count",
            "likes_count",
            "comments_count",
            "comments",
            "cover_image_url",
        ]

        read_only_fields = [
            "author_email",
            "published_at",
            "views_count",
            "likes_count",
            "comments_count",
            "comments",
            "cover_image_url",
        ]

    def get_cover_image_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None
