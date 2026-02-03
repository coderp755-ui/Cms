import traceback
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
import django.db
from django.http import Http404

from rest_framework import serializers, status
import rest_framework.exceptions
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.common.error_logs import log_error
from django.conf import settings


class ResponseHandlerMixin:
    """Standardized response handling for DRF APIViews.
    Provides methods for success, error, and exception responses.
    Integrates permission utilities for user permission checks.
    Usage:
        class SomeView(APIView, ResponseHandlerMixin):
            ...
            def get(self, request, *args, **kwargs):
                try:
                    # Your logic here
                    data = {...}
                    return self.success_response(data=data, message="Data retrieved successfully")
                except Exception as e:
                    return self.exception_response(e)

        under paginated_response the user permissions for the model are also added to each item in the response
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permission_utils = None

    def success_response(
        self,
        data=None,
        message="Success",
        status_code=status.HTTP_200_OK,
        **kwargs,
    ):
        """Return a standardized success response."""
        response_data = {"success": True, "message": message, **kwargs}
        module = self.__class__.__module__
        if data is not None:
            response_data["data"] = data
        return Response(response_data, status=status_code)

    def error_response(
        self,
        errors=None,
        message="Error",
        status_code=status.HTTP_400_BAD_REQUEST,
        **kwargs,
    ):
        """Return a standardized error response."""
        response_data = {"success": False, "message": message, **kwargs}
        module = self.__class__.__module__
        if errors is not None:
            response_data["errors"] = errors
        return Response(response_data, status=status_code)

    def exception_response(self, exc, message=None):
        """Handle common exceptions with appropriate responses."""

        module = (
            self.__class__.__module__
            if hasattr(self, "__class__")
            else "unknown_module"
        )
        api = self.request.path if hasattr(self, "request") else None

        exception_handlers = {
            ValidationError: lambda error: self.error_response(
                message="Validation Error" if message is None else message,
                errors=error.detail,
                status_code=status.HTTP_400_BAD_REQUEST,
            ),
            serializers.ValidationError: lambda error: self.error_response(
                message="Validation Error" if message is None else message,
                errors=error.detail,
                status_code=status.HTTP_400_BAD_REQUEST,
            ),
            PermissionDenied: lambda error: self.error_response(
                message="Permission Denied" if message is None else message,
                status_code=status.HTTP_403_FORBIDDEN,
            ),
            ObjectDoesNotExist: lambda error: self.error_response(
                message="Resource Not Found" if message is None else message,
                status_code=status.HTTP_404_NOT_FOUND,
            ),
            Http404: lambda error: self.error_response(
                message="Resource Not Found" if message is None else message,
                status_code=status.HTTP_404_NOT_FOUND,
            ),
            NotFound: lambda error: self.error_response(
                message="Resource Not Found" if message is None else message,
                status_code=status.HTTP_404_NOT_FOUND,
            ),
            MultipleObjectsReturned: lambda error: self.error_response(
                message=(
                    "Multiple objects found when one was expected"
                    if message is None
                    else message
                ),
                status_code=status.HTTP_409_CONFLICT,
            ),
            PermissionError: lambda error: self.error_response(
                message="Permission Error" if message is None else message,
                status_code=status.HTTP_403_FORBIDDEN,
            ),
            TimeoutError: lambda error: self.error_response(
                message="Request Timeout" if message is None else message,
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            ),
            ConnectionError: lambda error: self.error_response(
                message="Connection Error" if message is None else message,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ),
            ValueError: lambda error: self.error_response(
                message="Invalid Value" if message is None else message,
                errors=str(error),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            TypeError: lambda error: self.error_response(
                message="Type Error" if message is None else message,
                errors=str(error),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            KeyError: lambda error: self.error_response(
                message="Key Error" if message is None else message,
                errors=f"Missing key: {error}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            IndexError: lambda error: self.error_response(
                message="Index Error" if message is None else message,
                errors=str(error),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            AttributeError: lambda error: self.error_response(
                message="Attribute Error" if message is None else message,
                errors=str(error),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            # Django specific
            django.db.IntegrityError: lambda error: self.error_response(
                message="Database Integrity Error" if message is None else message,
                errors=str(error),
                status_code=status.HTTP_409_CONFLICT,
            ),
            django.db.DatabaseError: lambda error: self.error_response(
                message="Database Error" if message is None else message,
                errors=str(error),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            django.db.utils.OperationalError: lambda error: self.error_response(
                message="Database Operational Error" if message is None else message,
                errors=str(error),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            # DRF specific
            rest_framework.exceptions.AuthenticationFailed: lambda error: self.error_response(
                message="Authentication Failed" if message is None else message,
                errors=error.detail,
                status_code=status.HTTP_401_UNAUTHORIZED,
            ),
            rest_framework.exceptions.MethodNotAllowed: lambda error: self.error_response(
                message="Method Not Allowed" if message is None else message,
                errors=error.detail,
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            ),
            rest_framework.exceptions.Throttled: lambda error: self.error_response(
                message="Request Throttled" if message is None else message,
                errors=error.detail,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            ),
        }

        handler = exception_handlers.get(type(exc))
        log_error(
            str(traceback.format_exc()),
            model_name=module,
            user=getattr(self.request, "user", None),
            api=api,
        )
        if handler:
            return handler(exc)
        traceback.print_exc() if settings.DEBUG else None
        return self.error_response(
            message=f"Internal Server Error: {exc}" if message is None else message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def paginated_response(
        self,
        paginator,
        queryset,
        serializer_class,
        page=None,
        data=None,
        context=None,
        fields=None,
        exclude=None,
    ):
        """Handle paginated responses consistently using CustomPagination."""
        try:
            context = context or self.get_serializer_context()
            if page is None:
                page = paginator.paginate_queryset(queryset, self.request, view=self)
            if page is not None:
                try:
                    serializer = serializer_class(
                        page, fields=fields, exclude=exclude, many=True, context=context
                    )
                except TypeError:
                    serializer = serializer_class(page, many=True, context=context)

                serializer_data = serializer.data
                response_data = serializer_data  # Simplified without permission actions

                paginated_response = paginator.get_paginated_response(response_data)
                return self.success_response(
                    data=paginated_response.data.get("data", response_data),
                    message="Success",
                    meta=paginated_response.data.get("meta", {}),
                )

            # Handle non-paginated response
            try:
                serializer = serializer_class(
                    queryset, fields=fields, exclude=exclude, many=True, context=context
                )
            except TypeError:
                serializer = serializer_class(queryset, many=True, context=context)

            return self.success_response(data=serializer.data)
        except Exception as exc:
            traceback.print_exc() if settings.DEBUG else None
            log_error(
                exc,
                model_name=self.__class__.__module__,
                user=getattr(self.request, "user", None),
                api=self.request.path,
            )
            return self.exception_response(exc)
