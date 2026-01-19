# packages/urls.py
from django.urls import path
from .views import PackageListView, PackageDetailView

BASE = "packages"

urlpatterns = [
    path(f"{BASE}/", PackageListView.as_view(), name="package-list"),
    path(f"{BASE}/<int:id>/", PackageDetailView.as_view(), name="package-detail"),
]
