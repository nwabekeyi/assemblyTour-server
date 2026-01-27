from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import BlogPost, BlogComment, BlogReply

User = get_user_model()


# --------------------------
# LIST BLOG POSTS
# --------------------------
class BlogPostListSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    author_image_url = serializers.SerializerMethodField()
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


# --------------------------
# BLOG DETAIL
# --------------------------
class BlogPostDetailSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    author_image_url = serializers.SerializerMethodField()
    read_time = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)
    is_liked = serializers.SerializerMethodField()  # <-- NEW FIELD

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
            "is_liked",  # <-- include this in API
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

    def get_is_liked(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False

# --------------------------
# COMMENT SERIALIZER
# --------------------------
class BlogCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_img_url = serializers.SerializerMethodField()  # optional profile picture

    class Meta:
        model = BlogComment
        fields = [
            "id",
            "content",
            "user_name",
            "user_img_url",
            "created_at",
            "parent_id"
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_img_url(self, obj):
        request = self.context.get("request")
        if getattr(obj.user, "pic", None) and request:  # optional field
            return request.build_absolute_uri(obj.user.pic.url)
        return None

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class BlogReplySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_img_url = serializers.SerializerMethodField()
    comment_id = serializers.IntegerField(source="comment.id", read_only=True)

    class Meta:
        model = BlogReply
        fields = [
            "id",
            "content",
            "user_name",
            "user_img_url",
            "created_at",
            "comment_id",
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_img_url(self, obj):
        request = self.context.get("request")
        if getattr(obj.user, "pic", None) and request:
            return request.build_absolute_uri(obj.user.pic.url)
        return None
