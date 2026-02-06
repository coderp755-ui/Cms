from rest_framework import status, viewsets
from rest_framework.exceptions import MethodNotAllowed

from apps.common.response.mixins import ResponseHandlerMixin


class AbstractViewSet(
    viewsets.ModelViewSet,
    ResponseHandlerMixin,
):
    """Base ViewSet class with response handler mixin implemented.

    Required fields:
        - queryset
        - serializer_class

    For specific request methods use:
        - http_method_names

    For permissions classes use:
        - permission_classes
      Usage:
        class SomeView(APIView):
            permission_classes = [CustomPermissionClass]

    """

    exclude_methods = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.model_name = getattr(
                self, "model_name", self.get_queryset().model.__name__
            )
        except Exception:
            self.model_name = "Model"
        self.viewset_name = self.__class__.__name__

    def get_queryset(self):
        """Override to filter out soft-deleted items by default."""
        queryset = super().get_queryset()
        
        if hasattr(queryset.model, 'is_deleted'):
            queryset = queryset.filter(is_deleted=False)
        
        return queryset

    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() in self.exclude_methods:
            raise MethodNotAllowed(request.method)
        return super().dispatch(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())

            if self.pagination_class:
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(serializer.data)
        except Exception as e:
            return self.exception_response(e)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return self.success_response(
                message=f"{self.model_name} created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.exception_response(e)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.success_response(
                message=f"{self.model_name} retrieved successfully",
                data=serializer.data,
            )
        except Exception as e:
            return self.exception_response(e)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return self.success_response(
                message=f"{self.model_name} updated successfully", 
                data=serializer.data
            )
        except Exception as e:
            return self.exception_response(e)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)

            return self.success_response(
                message=f"{self.model_name} deleted successfully"
            )
        except Exception as e:
            return self.exception_response(e)