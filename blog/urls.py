from django.urls import path
from .views import (
    BlogPostListView,
    BlogPostDetailView,
    BlogCommentCreateView,
    BlogLikeToggleView,
)

urlpatterns = [
    path("blogs/", BlogPostListView.as_view(), name="blog-list"),
    path("blogs/<slug:slug>/", BlogPostDetailView.as_view(), name="blog-detail"),
    path("blogs/<int:post_id>/comment/", BlogCommentCreateView.as_view(), name="blog-comment"),
    path("blogs/<int:post_id>/like/", BlogLikeToggleView.as_view(), name="blog-like"),
]
