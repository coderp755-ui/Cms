from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response
from django.conf import settings

class CustomDefaultPagination(PageNumberPagination):
    """
    Common pagination used across all modules.
    """
    page_number_query = "page"
    page_size_query_param = "per_page"
    page_size = getattr(settings, 'DEFAULT_PAGE_SIZE', 10)
    max_page_size = getattr(settings, 'MAX_PAGE_SIZE', 100)

    
    def get_paginated_response(self, data):
        return Response(
            {
                "meta": {
                    "total": self.page.paginator.count,
                    "last_page": self.page.paginator.num_pages,
                    "current_page": self.page.number,
                    "per_page": self.page.paginator.per_page,
                },
                "data": data,
            }
        )


class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 10
    limit_query_param = "limit"
    offset_query_param = "offset"

    def get_paginated_response(self, data):
        return Response(
            {
                "success": True,
                "message": "Success",
                "count": self.count,
                "data": data,
            }
        )