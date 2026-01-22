from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from core.utils.api_response import api_response
from core.utils.pagination import StandardResultsSetPagination
from .models import Package
from .serializers import PackageSerializer


class PackageListView(generics.ListAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={"request": request}
            )
            paginated_data = self.get_paginated_response(serializer.data).data
            return api_response(
                data=paginated_data,
                message="Packages retrieved successfully",
            )

        serializer = self.get_serializer(
            queryset,
            many=True,
            context={"request": request}
        )
        return api_response(
            data=serializer.data,
            message="Packages retrieved successfully",
        )


class PackageDetailView(generics.RetrieveAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    lookup_field = "id"
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        package = self.get_object()
        serializer = self.get_serializer(
            package,
            context={"request": request}
        )
        return api_response(
            data=serializer.data,
            message="Package details retrieved successfully",
        )

