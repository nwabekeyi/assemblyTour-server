from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, F
from django.db import transaction
from core.utils.api_response import api_response
from core.utils.pagination import StandardResultsSetPagination
from .models import BlogPost, BlogLike, BlogComment, BlogReply, BlogViewer
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogCommentSerializer,
    BlogReplySerializer,
)
from .validators import BlogCommentCreateData, BlogLikeToggleData, validate_or_raise


# ───────────────────────────────────────────────
# LIST BLOG POSTS (unchanged)
# ───────────────────────────────────────────────
class BlogPostListView(generics.ListAPIView):
    serializer_class = BlogPostListSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = BlogPost.objects.filter(is_published=True).annotate(
            comments_count=Count("comments", distinct=True),
            popularity=F("likes_count") + Count("comments", distinct=True),
        )

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(
                excerpt__icontains=search
            ) | queryset.filter(author_name__icontains=search)

        sort = self.request.query_params.get("sort")
        if sort == "popular":
            return queryset.order_by("-popularity", "-published_at")
        return queryset.order_by("-published_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data
            return api_response(data=paginated_data, message="Blog posts fetched successfully")

        serializer = self.get_serializer(queryset, many=True)
        return api_response(data=serializer.data, message="Blog posts fetched successfully")


# ───────────────────────────────────────────────
# BLOG DETAIL + TRACK VIEWERS (unchanged)
# ───────────────────────────────────────────────
class BlogPostDetailView(generics.RetrieveAPIView):
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostDetailSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Track viewers
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key

        viewer_exists = BlogViewer.objects.filter(
            post=instance,
            user=user,
            session_id=None if user else session_id
        ).exists()

        if not viewer_exists:
            BlogViewer.objects.create(
                post=instance,
                user=user,
                session_id=None if user else session_id,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            instance.views_count = F("views_count") + 1
            instance.save(update_fields=["views_count"])

        instance.refresh_from_db()

        liked = False
        if request.user.is_authenticated:
            liked = BlogLike.objects.filter(post=instance, user=request.user).exists()

        serializer = self.get_serializer(instance)
        data = serializer.data
        data["liked_by_user"] = liked

        return api_response(data=data, message="Blog post fetched successfully")


# ───────────────────────────────────────────────
# CREATE COMMENT – FIXED: context passed
# ───────────────────────────────────────────────
class BlogCommentCreateView(generics.CreateAPIView):
    serializer_class = BlogCommentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        post = get_object_or_404(BlogPost, id=self.kwargs["post_id"])
        validated_input = validate_or_raise(request.data, BlogCommentCreateData)

        # Create comment
        serializer = self.get_serializer(data={"content": validated_input.content})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(post=post, user=request.user)

        # Re-serialize with context so user_name & user_img_url are correct
        output_serializer = self.get_serializer(comment, context=self.get_serializer_context())
        return api_response(data=output_serializer.data, message="Comment added successfully")


# ───────────────────────────────────────────────
# EDIT COMMENT (unchanged – already correct)
# ───────────────────────────────────────────────
class BlogCommentEditView(generics.UpdateAPIView):
    queryset = BlogComment.objects.all()
    serializer_class = BlogCommentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.user != request.user:
            return api_response(message="You cannot edit this comment", status_code=403)
        serializer = self.get_serializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_response(data=serializer.data, message="Comment updated successfully")


# ───────────────────────────────────────────────
# DELETE COMMENT (unchanged)
# ───────────────────────────────────────────────
class BlogCommentDeleteView(generics.DestroyAPIView):
    queryset = BlogComment.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.user != request.user:
            return api_response(message="You cannot delete this comment", status_code=403)
        comment.delete()
        return api_response(message="Comment deleted successfully")


# ───────────────────────────────────────────────
# LIST COMMENTS BY SLUG (unchanged – context auto-included in ListAPIView)
# ───────────────────────────────────────────────
class BlogCommentListBySlugView(generics.ListAPIView):
    serializer_class = BlogCommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        post = get_object_or_404(BlogPost, slug=self.kwargs["slug"])
        return BlogComment.objects.filter(post=post).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(data=serializer.data, message="Comments fetched successfully")


# ───────────────────────────────────────────────
# CREATE REPLY – FIXED: context passed
# ───────────────────────────────────────────────
class BlogReplyCreateView(generics.CreateAPIView):
    serializer_class = BlogReplySerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        comment = get_object_or_404(BlogComment, id=self.kwargs["comment_id"])
        content = request.data.get("content", "").strip()
        if not content:
            return api_response(message="Reply cannot be empty", status_code=400)

        reply = BlogReply.objects.create(
            comment=comment,
            user=request.user,
            content=content,
        )

        # FIX: serialize with context so user_name & user_img_url work
        serializer = self.get_serializer(reply, context=self.get_serializer_context())
        return api_response(data=serializer.data, message="Reply added successfully")


# ───────────────────────────────────────────────
# EDIT REPLY (unchanged – already correct)
# ───────────────────────────────────────────────
class BlogReplyEditView(generics.UpdateAPIView):
    queryset = BlogReply.objects.all()
    serializer_class = BlogReplySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        reply = self.get_object()
        if reply.user != request.user:
            return api_response(message="You cannot edit this reply", status_code=403)
        serializer = self.get_serializer(reply, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_response(data=serializer.data, message="Reply updated successfully")


# ───────────────────────────────────────────────
# DELETE REPLY (unchanged)
# ───────────────────────────────────────────────
class BlogReplyDeleteView(generics.DestroyAPIView):
    queryset = BlogReply.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def destroy(self, request, *args, **kwargs):
        reply = self.get_object()
        if reply.user != request.user:
            return api_response(message="You cannot delete this reply", status_code=403)
        reply.delete()
        return api_response(message="Reply deleted successfully")


# ───────────────────────────────────────────────
# LIST REPLIES (unchanged – context auto-included)
# ───────────────────────────────────────────────
class BlogReplyListView(generics.ListAPIView):
    serializer_class = BlogReplySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        comment = get_object_or_404(BlogComment, id=self.kwargs["comment_id"])
        return BlogReply.objects.filter(comment=comment).order_by("created_at")

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_response(data=serializer.data, message="Replies fetched successfully")


# ───────────────────────────────────────────────
# TOGGLE LIKE / UNLIKE (unchanged)
# ───────────────────────────────────────────────
class BlogLikeToggleView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        validate_or_raise(request.data or {}, BlogLikeToggleData)
        post = get_object_or_404(BlogPost, id=post_id)

        with transaction.atomic():
            like, created = BlogLike.objects.get_or_create(post=post, user=request.user)
            if created:
                post.likes_count = F("likes_count") + 1
                action = "liked"
            else:
                like.delete()
                post.likes_count = F("likes_count") - 1
                action = "unliked"
            post.save(update_fields=["likes_count"])
            post.refresh_from_db()

        return api_response(
            data={"likes_count": post.likes_count},
            message=f"Blog post successfully {action}",
        )   