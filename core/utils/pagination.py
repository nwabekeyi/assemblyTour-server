from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # default items per page
    page_size_query_param = "limit"  # allow client to set page size
    max_page_size = 50
    page_query_param = "page"

    def get_paginated_response(self, data):
        """
        Wrap paginated data into a standard API response
        """
        return Response({
            "success": True,
            "message": "Data fetched successfully",
            "data": data,
            "pagination": {
                "current_page": self.page.number,
                "total_pages": self.page.paginator.num_pages,
                "total_items": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page_size": self.get_page_size(self.request)
            },
            "errors": None
        })
