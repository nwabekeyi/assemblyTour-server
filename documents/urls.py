from django.urls import path
from .views import (
    DocumentListCreateView,
    DocumentDetailView,
    DocumentTypeListView,
)

urlpatterns = [
    path('document-types/', DocumentTypeListView.as_view(), name='document-types-list'),
    path('documents/', DocumentListCreateView.as_view(), name='documents-list-create'),
    path('documents/<str:pk>/', DocumentDetailView.as_view(), name='document-detail'),
]
