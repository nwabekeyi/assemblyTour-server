from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core.utils.api_response import api_response
from core.utils.pagination import StandardResultsSetPagination
from .models import SacredSite
from .serializers import SacredSiteSerializer


class SacredSiteListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        queryset = SacredSite.objects.filter(is_active=True).order_by("id")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        serializer = SacredSiteSerializer(page, many=True)

        # paginator.get_paginated_response returns a DRF Response
        paginated_data = paginator.get_paginated_response(serializer.data).data

        return api_response(
            data=paginated_data,
            message="Sacred sites fetched successfully"
        )
