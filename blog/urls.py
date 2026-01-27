from django.urls import path
from .views import (
    BlogPostListView,
    BlogPostDetailView,
    BlogCommentCreateView,
    BlogCommentDeleteView,
    BlogCommentEditView,
    BlogCommentListBySlugView,
    BlogReplyCreateView,
    BlogReplyListView,
    BlogReplyDeleteView,
    BlogReplyEditView,
    BlogLikeToggleView,
)

urlpatterns = [
    # ──────────────── BLOG ────────────────
    path("blogs/", BlogPostListView.as_view(), name="blog-list"),
    path("blogs/<slug:slug>/", BlogPostDetailView.as_view(), name="blog-detail"),

    # ──────────────── LIKES ────────────────
    path("blogs/<str:post_id>/like/", BlogLikeToggleView.as_view(), name="blog-like"),

    # ──────────────── COMMENTS ────────────────
    path("blogs/<str:post_id>/comments/post/", BlogCommentCreateView.as_view(), name="blog-comment-create"),
    path("blogs/comments/<str:id>/edit/", BlogCommentEditView.as_view(), name="blog-comment-edit"),
    path("blogs/comments/<str:id>/delete/", BlogCommentDeleteView.as_view(), name="blog-comment-delete"),
    path("blogs/<slug:slug>/comments/", BlogCommentListBySlugView.as_view(), name="blog-comment-list"),

    # ──────────────── REPLIES ────────────────
    path("blogs/comments/<str:comment_id>/reply/", BlogReplyCreateView.as_view(), name="blog-reply-create"),
    path("blogs/comments/<str:comment_id>/replies/", BlogReplyListView.as_view(), name="blog-reply-list"),
    path("blogs/replies/<str:id>/edit/", BlogReplyEditView.as_view(), name="blog-reply-edit"),
    path("blogs/replies/<str:id>/delete/", BlogReplyDeleteView.as_view(), name="blog-reply-delete"),
]
