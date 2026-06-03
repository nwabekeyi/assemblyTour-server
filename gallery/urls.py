from django.urls import path
from .views import GalleryDetailView, GalleryListView

urlpatterns = [
    path("gallery/", GalleryListView.as_view(), name="gallery-list"),
    path("gallery/<slug:slug>/", GalleryDetailView.as_view(), name="gallery-detail"),
]
