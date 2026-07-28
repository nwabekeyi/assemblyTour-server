from django.urls import path
from .views import GalleryDetailView, GalleryListView, GalleryCreateView, GalleryUpdateView, GalleryDeleteView

urlpatterns = [
    path("gallery/", GalleryListView.as_view(), name="gallery-list"),
    path("gallery/create/", GalleryCreateView.as_view(), name="gallery-create"),
    path("gallery/<slug:slug>/", GalleryDetailView.as_view(), name="gallery-detail"),
    path("gallery/<slug:slug>/update/", GalleryUpdateView.as_view(), name="gallery-update"),
    path("gallery/<slug:slug>/delete/", GalleryDeleteView.as_view(), name="gallery-delete"),
]
