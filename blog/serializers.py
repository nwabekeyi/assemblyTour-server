from rest_framework import serializers
from .models import BlogPost, BlogComment


class BlogPostListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "cover_image_url",
            "author_name",
            "published_at",
            "views_count",
            "likes_count",
        ]

    def get_author_name(self, obj):
        return obj.author.full_name if obj.author else "Admin"


class BlogPostDetailSerializer(serializers.ModelSerializer):
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = BlogPost
        fields = "__all__"


class BlogCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = ["id", "content", "user_name", "created_at"]

    def get_user_name(self, obj):
        return obj.user.email

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
