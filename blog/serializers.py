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
    user_img_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = [
            "id",
            "post",                     # optional — can be read_only
            "content",
            "user_name",
            "user_img_url",
            "created_at",
            "parent",                   # if using threaded comments
        ]
        read_only_fields = [
            "id", "created_at", "user_name", "user_img_url", "post"
        ]

    def get_user_name(self, obj):
        if not obj.user:
            return "Deleted User"
    # Use username as fallback, optionally phone
        return obj.user.username or obj.user.phone or "Anonymous"


    def get_user_img_url(self, obj):
        request = self.context.get("request")
        if obj.user and obj.user.profile_picture:
            url = obj.user.profile_picture
            return request.build_absolute_uri(url) if request else url

    # Nice fallback using ui-avatars.com (no extra storage needed)
        name = obj.user.get_full_name() or obj.user.username or "User"
        return f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=random"

    def create(self, validated_data):
        # user is always set from request
        validated_data["user"] = self.context["request"].user
        # post is usually set in the view
        return super().create(validated_data)


# ────────────────────────────────────────────────
# REPLY SERIALIZER
# ────────────────────────────────────────────────
class BlogReplySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_img_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogReply
        fields = [
            "id",
            "comment",                  # read_only in most cases
            "content",
            "user_name",
            "user_img_url",
            "created_at",
        ]
        read_only_fields = [
            "id", "created_at", "user_name", "user_img_url", "comment"
        ]

    def get_user_name(self, obj):
        if not obj.user:
            return "Deleted User"
    # Use username as fallback, optionally phone
        return obj.user.username or obj.user.phone or "Anonymous"

    def get_user_img_url(self, obj):
        request = self.context.get("request")
        if obj.user and obj.user.profile_picture:
            url = obj.user.profile_picture
            return request.build_absolute_uri(url) if request else url

    # Nice fallback using ui-avatars.com (no extra storage needed)
        name = obj.user.get_full_name() or obj.user.username or "User"
        return f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=random"


