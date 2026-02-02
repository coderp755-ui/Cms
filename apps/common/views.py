from django.shortcuts import render

# Create your views here.
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from common_utils.response.mixins import  ResponseHandlerMixin

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
        self.model_name = getattr(
            self, "model_name", self.get_queryset().model.__name__
        )
        self.viewset_name = self.__class__.__name__
        self.permission_utils = None

    def initial(self, request, *args, **kwargs):
        request = self.request
        self.permission_utils = PermissionUtils(request.user, self.model_name, view=self, request=request)
        if request and hasattr(request, "user") and request.user.is_authenticated:
            self.user_all_permissions = self.permission_utils.get_user_all_permissions()
            self.available_actions = self.permission_utils.user_available_actions()
            self.user_module_permissions = self.permission_utils.get_user_model_permissions()
        return super().initial(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() in self.exclude_methods:
            raise MethodNotAllowed(request.method)
        return super().dispatch(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            if self.pagination_class:
                page = self.paginate_queryset(queryset)
                return self.paginated_response(
                    paginator=self.paginator,
                    queryset=queryset,
                    serializer_class=self.get_serializer_class(),
                    page=page,
                    context=self.get_serializer_context(),
                )
            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(serializer.data)
        except Exception as e:
            return self.exception_response(e)

    # @method_decorator(csrf_protect)
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.save()
            data.created_by = request.user if hasattr(request, "user") else None
            # self.perform_create(serializer)

            data.save()
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

    # @method_decorator(csrf_protect)
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.save()
            data.updated_by = request.user if hasattr(request, "user") else None
            data.save()
            # self.perform_update(serializer)

            # if getattr(instance, "_prefetched_objects_cache", None):
            #     # If 'prefetch_related' has been applied to a queryset, we need to
            #     # forcibly invalidate the prefetch cache on the instance.
            #     instance._prefetched_objects_cache = {}
            return self.success_response(
                message=f"{self.model_name} updated successfully", data=serializer.data
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

    # @method_decorator(csrf_protect)
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if hasattr(instance, "is_deleted"):
                instance.delete(user = request.user)
            elif hasattr(instance, "is_active"):
                instance.is_active = False
            else:
                return self.error_response(
                    message=f"{self.model_name} Couldnt be deleted"
                )
            instance.save()
            # self.perform_destroy(instance)
            return self.success_response(
                message=f"{self.model_name} deleted successfully",
                # status_code=status.HTTP_204_NO_CONTENT,
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
