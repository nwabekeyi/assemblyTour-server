from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Package
from .serializers import PackageSerializer
from core.utils.api_response import api_response
from rest_framework.permissions import AllowAny



class PackageListView(generics.ListAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        packages = self.get_queryset()
        serializer = self.get_serializer(packages, many=True)
        return api_response(
            success=True,
            message="Packages retrieved successfully",
            data=serializer.data,
            errors=None,
            status_code=status.HTTP_200_OK
        )


class PackageDetailView(generics.RetrieveAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    lookup_field = "id"
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        package = self.get_object()
        serializer = self.get_serializer(package)
        return api_response(
            success=True,
            message="Package details retrieved successfully",
            data=serializer.data,
            errors=None,
            status_code=status.HTTP_200_OK
        )
