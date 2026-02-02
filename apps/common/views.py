from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_protect

from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.common.response.mixins import ResponseHandlerMixin

from rest_framework.exceptions import MethodNotAllowed


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
    exclude_methods = []          # class-level
    exclude_actions = []          # optional, explained below

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only set model_name if queryset is available
        try:
            self.model_name = getattr(
                self, "model_name", self.get_queryset().model.__name__
            )
        except:
            self.model_name = getattr(self, "model_name", "Model")
        self.viewset_name = self.__class__.__name__
        self.permission_utils = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # Skip permission utils for now since it's not defined
        pass

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
            
            # Save the instance
            instance = serializer.save()
            
            # Set audit fields if they exist
            if hasattr(instance, 'created_by') and hasattr(request, "user") and request.user.is_authenticated:
                instance.created_by = request.user
                instance.save()

            return self.success_response(
                message=f"{self.model_name} created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
            )
        except (
            ValidationError,
            NotFound,
            ObjectDoesNotExist,
            PermissionDenied,
            Http404,
        ) as e:
            return self.exception_response(e)
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
        except (
            ValidationError,
            PermissionDenied,
            ObjectDoesNotExist,
            Http404,
            NotFound,
        ) as e:
            return self.exception_response(e)
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
            
            # Save the instance
            updated_instance = serializer.save()
            
            # Set audit fields if they exist
            if hasattr(updated_instance, 'updated_by') and hasattr(request, "user") and request.user.is_authenticated:
                updated_instance.updated_by = request.user
                updated_instance.save()

            return self.success_response(
                message=f"{self.model_name} updated successfully", 
                data=serializer.data
            )
        except (
            ObjectDoesNotExist,
            Http404,
            NotFound,
            ValidationError,
            PermissionDenied,
        ) as e:
            return self.exception_response(e)
        except Exception as e:
            return self.exception_response(e)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # Check if soft delete is available
            if hasattr(instance, "soft_delete"):
                instance.soft_delete()
            elif hasattr(instance, "is_deleted"):
                instance.is_deleted = True
                instance.save()
            elif hasattr(instance, "is_active"):
                instance.is_active = False
                instance.save()
            else:
                # Hard delete as fallback
                instance.delete()
            
            return self.success_response(
                message=f"{self.model_name} deleted successfully"
            )
        except (
            ObjectDoesNotExist,
            Http404,
            NotFound,
            ValidationError,
            PermissionDenied,
        ) as e:
            return self.exception_response(e)
        except Exception as e:
            return self.exception_response(e)
