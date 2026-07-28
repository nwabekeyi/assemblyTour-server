from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from core.utils.api_response import api_response
from core.utils.pagination import StandardResultsSetPagination
from core.services.cloudinary_service import CloudinaryService

from .models import Gallery
from .serializers import GallerySerializer


cloudinary_service = CloudinaryService()


class GalleryListView(generics.ListAPIView):
    serializer_class = GallerySerializer
    permission_classes = [permissions.AllowAny]
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
    permission_classes = [permissions.AllowAny]
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


class GalleryCreateView(generics.CreateAPIView):
    serializer_class = GallerySerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        media_type = data.get("media_type")

        thumbnail_file = request.FILES.get("thumbnail")
        media_file = request.FILES.get("media")

        if media_type == "youtube":
            if not data.get("url"):
                return api_response(
                    success=False,
                    message="YouTube URL is required for YouTube media type",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        elif media_type == "video":
            if not media_file and not data.get("url"):
                return api_response(
                    success=False,
                    message="Video file or URL is required for video media type",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if not thumbnail_file:
                return api_response(
                    success=False,
                    message="Thumbnail is required for video media type",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        elif media_type == "image":
            if not media_file:
                return api_response(
                    success=False,
                    message="Image file is required for image media type",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            data.pop("thumbnail", None)
            thumbnail_file = None
        else:
            return api_response(
                success=False,
                message="Invalid media type",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if thumbnail_file:
            try:
                upload_result = cloudinary_service.upload(thumbnail_file, subfolder="gallery/thumbnails")
                data["thumbnail_public_id"] = upload_result.get("public_id")
                data["thumbnail"] = upload_result.get("secure_url") or upload_result.get("url")
            except Exception as exc:
                return api_response(
                    success=False,
                    message="Failed to upload thumbnail",
                    errors={"detail": [str(exc)]},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if media_file:
            try:
                upload_result = cloudinary_service.upload(media_file, subfolder="gallery/media")
                data["media_public_id"] = upload_result.get("public_id")
                data["media"] = upload_result.get("secure_url") or upload_result.get("url")
                if not data.get("url"):
                    data["url"] = upload_result.get("secure_url") or upload_result.get("url")
            except Exception as exc:
                return api_response(
                    success=False,
                    message="Failed to upload media",
                    errors={"detail": [str(exc)]},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)

        return api_response(
            data=serializer.data,
            message="Gallery item created successfully",
            status_code=status.HTTP_201_CREATED,
        )


class GalleryUpdateView(generics.UpdateAPIView):
    serializer_class = GallerySerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field = "slug"

    def get_queryset(self):
        return Gallery.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        media_type = data.get("media_type", instance.media_type)

        thumbnail_file = request.FILES.get("thumbnail")
        media_file = request.FILES.get("media")

        if media_type == "youtube":
            if not data.get("url"):
                return api_response(
                    success=False,
                    message="YouTube URL is required for YouTube media type",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        elif media_type == "video":
            if thumbnail_file:
                try:
                    upload_result = cloudinary_service.upload(thumbnail_file, subfolder="gallery/thumbnails")
                    if instance.thumbnail_public_id:
                        try:
                            cloudinary_service.delete(instance.thumbnail_public_id)
                        except Exception:
                            pass
                    data["thumbnail_public_id"] = upload_result.get("public_id")
                    data["thumbnail"] = upload_result.get("secure_url") or upload_result.get("url")
                except Exception as exc:
                    return api_response(
                        success=False,
                        message="Failed to upload thumbnail",
                        errors={"detail": [str(exc)]},
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
        elif media_type == "image":
            data.pop("thumbnail", None)
            data["thumbnail"] = None
            data["thumbnail_public_id"] = None
            if media_file:
                try:
                    upload_result = cloudinary_service.upload(media_file, subfolder="gallery/media")
                    if instance.media_public_id:
                        try:
                            cloudinary_service.delete(instance.media_public_id)
                        except Exception:
                            pass
                    data["media_public_id"] = upload_result.get("public_id")
                    data["media"] = upload_result.get("secure_url") or upload_result.get("url")
                    if not data.get("url"):
                        data["url"] = upload_result.get("secure_url") or upload_result.get("url")
                except Exception as exc:
                    return api_response(
                        success=False,
                        message="Failed to upload media",
                        errors={"detail": [str(exc)]},
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return api_response(
            data=serializer.data,
            message="Gallery item updated successfully",
        )


class GalleryDeleteView(generics.DestroyAPIView):
    serializer_class = GallerySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        return Gallery.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.thumbnail_public_id:
            try:
                cloudinary_service.delete(instance.thumbnail_public_id)
            except Exception:
                pass

        if instance.media_public_id:
            try:
                cloudinary_service.delete(instance.media_public_id)
            except Exception:
                pass

        instance.delete()

        return api_response(message="Gallery item deleted successfully")
