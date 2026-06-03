from rest_framework import generics
from rest_framework.permissions import AllowAny

from core.utils.api_response import api_response
from core.utils.pagination import StandardResultsSetPagination
from .models import Gallery
from .serializers import GallerySerializer


class GalleryListView(generics.ListAPIView):
    serializer_class = GallerySerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Gallery.objects.filter(is_active=True)
        media_type = self.request.query_params.get("media_type")
        if media_type:
            queryset = queryset.filter(media_type__iexact=media_type)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data
            return api_response(
                data=paginated_data,
                message="Gallery retrieved successfully",
            )

        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            data=serializer.data,
            message="Gallery retrieved successfully",
        )


class GalleryDetailView(generics.RetrieveAPIView):
    serializer_class = GallerySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return Gallery.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        gallery = self.get_object()
        serializer = self.get_serializer(gallery)
        return api_response(
            data=serializer.data,
            message="Gallery item retrieved successfully",
        )
