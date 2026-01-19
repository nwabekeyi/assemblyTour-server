from django.urls import path
from .views import (
    BlogPostListView,
    BlogPostCreateView,
    BlogPostDetailView,
    BlogCommentCreateView,
    BlogLikeToggleView,
)

urlpatterns = [
    path("posts/", BlogPostListView.as_view()),
    path("posts/create/", BlogPostCreateView.as_view()),
    path("posts/<slug:slug>/", BlogPostDetailView.as_view()),

    path("posts/<uuid:post_id>/comments/", BlogCommentCreateView.as_view()),
    path("posts/<uuid:post_id>/like/", BlogLikeToggleView.as_view()),
]
