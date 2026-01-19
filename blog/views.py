from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import BlogPost, BlogComment, BlogLike
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogCommentSerializer,
)
from .permissions import IsAdminUserOnly


# LIST BLOG POSTS (PUBLIC)
class BlogPostListView(generics.ListAPIView):
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostListSerializer
    permission_classes = [AllowAny]


# CREATE BLOG POST (ADMIN ONLY)
class BlogPostCreateView(generics.CreateAPIView):
    serializer_class = BlogPostDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOnly]

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            published_at=timezone.now()
        )


# BLOG DETAIL
class BlogPostDetailView(generics.RetrieveAPIView):
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=["views_count"])
        return super().retrieve(request, *args, **kwargs)


# COMMENTS
class BlogCommentCreateView(generics.CreateAPIView):
    serializer_class = BlogCommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post = get_object_or_404(BlogPost, id=self.kwargs["post_id"])
        serializer.save(post=post)


# LIKE / UNLIKE
class BlogLikeToggleView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(BlogPost, id=post_id)
        like, created = BlogLike.objects.get_or_create(
            post=post,
            user=request.user
        )

        if not created:
            like.delete()
            post.likes_count -= 1
        else:
            post.likes_count += 1

        post.save(update_fields=["likes_count"])
        return Response({"likes_count": post.likes_count})
