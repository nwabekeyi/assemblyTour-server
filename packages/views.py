from rest_framework import generics
from rest_framework.permissions import AllowAny
from core.utils.api_response import api_response
from core.utils.pagination import StandardResultsSetPagination
from .models import Package
from .serializers import PackageSerializer, PackageNavbarSerializer


class PackageListView(generics.ListAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Optionally filter packages by category.
        If ?category=Umrah or ?category=Hajj is provided, filter.
        Otherwise, return all packages.
        """
        queryset = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__iexact=category)
        return queryset

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


class PackageNavbarOverviewView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Fetch all packages
        packages = Package.objects.all()

        # Split into two categories
        umrah_packages = packages.filter(category="umrah")
        hajj_packages = packages.filter(category="hajj")

        # Serialize only id, name, type
        umrah_data = PackageNavbarSerializer(
            umrah_packages, many=True, context={"request": request}
        ).data
        hajj_data = PackageNavbarSerializer(
            hajj_packages, many=True, context={"request": request}
        ).data

        return api_response(
            data={
                "umrah": umrah_data,
                "hajj": hajj_data
            },
            message="Navbar overview retrieved successfully"
        )