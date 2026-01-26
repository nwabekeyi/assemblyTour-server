from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from core.utils.api_response import api_response
from core.utils.pagination import StandardResultsSetPagination
from .models import BlogPost, BlogLike, BlogComment
from .serializers import BlogPostListSerializer, BlogPostDetailSerializer, BlogCommentSerializer
from django.db.models import Count, F

# --------------------------
# LIST BLOG POSTS (PAGINATED)
# --------------------------
class BlogPostListView(generics.ListAPIView):
    serializer_class = BlogPostListSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            BlogPost.objects
            .filter(is_published=True)
            .annotate(
                comments_count=Count("comments", distinct=True),
                popularity=F("likes_count") + Count("comments", distinct=True)
            )
        )

        # 🔍 SEARCH
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                title__icontains=search
            ) | queryset.filter(
                excerpt__icontains=search
            ) | queryset.filter(
                author_name__icontains=search
            )

        # 🔥 SORT
        sort = self.request.query_params.get("sort")

        if sort == "popular":
            queryset = queryset.order_by("-popularity", "-published_at")
        else:
            queryset = queryset.order_by("-published_at")

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data
            return api_response(
                data=paginated_data,
                message="Blog posts fetched successfully"
            )

        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            data=serializer.data,
            message="Blog posts fetched successfully"
        )


# --------------------------
# BLOG DETAIL
# --------------------------
class BlogPostDetailView(generics.RetrieveAPIView):
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostDetailSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=["views_count"])

        serializer = self.get_serializer(instance)
        return api_response(
            data=serializer.data,
            message="Blog post fetched successfully"
        )


# --------------------------
# COMMENT CREATE
# --------------------------
class BlogCommentCreateView(generics.CreateAPIView):
    serializer_class = BlogCommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post = get_object_or_404(BlogPost, id=self.kwargs["post_id"])
        serializer.save(post=post)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return api_response(
            data=response.data,
            message="Comment added successfully",
            status=status.HTTP_201_CREATED
        )


# --------------------------
# LIKE / UNLIKE TOGGLE
# --------------------------
class BlogLikeToggleView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(BlogPost, id=post_id)
        like, created = BlogLike.objects.get_or_create(post=post, user=request.user)

        if not created:
            like.delete()
            post.likes_count = max(post.likes_count - 1, 0)
            action = "unliked"
        else:
            post.likes_count += 1
            action = "liked"

        post.save(update_fields=["likes_count"])
        return api_response(
            data={"likes_count": post.likes_count},
            message=f"Blog post successfully {action}"
        )


class BlogCommentListBySlugView(generics.ListAPIView):
    serializer_class = BlogCommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        post = get_object_or_404(BlogPost, slug=slug)
        return BlogComment.objects.filter(post=post).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            data=serializer.data,
            message="Comments fetched successfully"
        )