"""
Views with role-based permissions using AbstractViewSet.
AbstractViewSet handles: list, create, retrieve, update, destroy, created_by, updated_by
"""

from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from apps.common.views import AbstractViewSet
from apps.common.response.mixins import ResponseHandlerMixin
from apps.common.paginations.default_paginations import CustomDefaultPagination
from apps.acounts.models import User, UserProfile, StudentProfile, TeacherProfile
from apps.acounts.Serializers.account_serializers import (
    Self,
    UserSerializer,
    UserProfileSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
)
from apps.acounts.permissions import (
    IsAdmin,
    IsTeacher,
)
from apps.acounts.filters import (
    UserFilterSet,
    StudentProfileFilterSet,
    TeacherProfileFilterSet,
)


class UserViewSet(AbstractViewSet):
    """
    ViewSet for User model with CRUD operations and role-based functionality.

    Permissions:
    - Superadmin: Full access - can add/edit/delete all users
    - Admin: Can add/edit/delete teachers and students (cannot manage superadmins)
    - Teacher: Can add students only, can view students and teachers
    - Student: Can view and update only their own profile
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filterset_class = UserFilterSet
    search_fields = [
        "first_name",
        "last_name",
        "username",
        "email",
        "employee_id",
        "student_id",
    ]
    ordering_fields = [
        "id",
        "username",
        "first_name",
        "last_name",
        "date_joined",
        "role",
    ]
    ordering = ["-date_joined"]

    def get_queryset(self):
        """Filter queryset based on user role and permissions."""
        # Exclude superadmin by default (is_deleted filter handled by AbstractViewSet)
        queryset = super().get_queryset().exclude(role="superadmin")

        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()

        # Superadmin can see all users (including other superadmins)
        if user.role == "superadmin":
            return User.objects.all()
        # Admin can see all except superadmin
        elif user.role == "admin":
            return queryset
        # Teachers can see students and teachers only
        elif user.role == "teacher":
            return queryset.filter(role__in=["student", "teacher"])
        # Students can only see themselves
        elif user.role == "student":
            return queryset.filter(id=user.id)

        return queryset.none()

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def change_password(self, request):
        """Change user password."""
        try:
            old_password = request.data.get("old_password")
            new_password = request.data.get("new_password")

            if not old_password or not new_password:
                return self.error_response(
                    message="Both old_password and new_password are required"
                )

            user = request.user
            if not user.check_password(old_password):
                return self.error_response(message="Old password is incorrect")

            user.set_password(new_password)
            user.save()

            return self.success_response(message="Password changed successfully")
        except Exception as e:
            return self.exception_response(e)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated, IsAdmin],
    )
    def by_role(self, request):
        """Get users filtered by role. Only superadmin and admin can use this."""
        try:
            role = request.query_params.get("role")
            if not role:
                return self.error_response(message="Role parameter is required")

            if request.user.role == "admin" and role == "superadmin":
                return self.error_response(
                    message="You don't have permission to view superadmin users",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            queryset = self.get_queryset().filter(role=role)
            serializer = self.get_serializer(queryset, many=True)

            return self.success_response(
                message=f"Users with role '{role}' retrieved successfully",
                data=serializer.data,
            )
        except Exception as e:
            return self.exception_response(e)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, IsAdmin],
    )
    def activate(self, request, pk=None):
        """Activate a user account. Only superadmin and admin can activate users."""
        try:
            user = self.get_object()

            if request.user.role == "admin" and user.role == "superadmin":
                return self.error_response(
                    message="You don't have permission to activate superadmin users",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            user.is_active = True
            user.save()

            return self.success_response(
                message=f"User {user.username} activated successfully"
            )
        except Exception as e:
            return self.exception_response(e)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, IsAdmin],
    )
    def deactivate(self, request, pk=None):
        """Deactivate a user account. Only superadmin and admin can deactivate users."""
        try:
            user = self.get_object()

            if request.user.role == "admin" and user.role == "superadmin":
                return self.error_response(
                    message="You don't have permission to deactivate superadmin users",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            if user.id == request.user.id:
                return self.error_response(
                    message="You cannot deactivate your own account",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            user.is_active = False
            user.save()

            return self.success_response(
                message=f"User {user.username} deactivated successfully"
            )
        except Exception as e:
            return self.exception_response(e)


class UserProfileViewSet(AbstractViewSet):
    """
    ViewSet for UserProfile model.

    Permissions:
    - Superadmin & Admin: Full access to all profiles
    - Teacher: Can view all student/teacher profiles, can update own profile
    - Student: Can view and update only their own profile
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomDefaultPagination

    def get_queryset(self):
        """Filter profiles based on user permissions."""
        queryset = super().get_queryset()

        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role in ["superadmin", "admin"]:
            return queryset
        elif user.role == "teacher":
            return queryset.filter(user__role__in=["student", "teacher"])
        elif user.role == "student":
            return queryset.filter(user=user)

        return queryset.none()

    def perform_update(self, serializer):
        """Validate user can only update their own profile unless admin."""
        user = self.request.user
        instance = self.get_object()

        if user.role in ["student", "teacher"] and instance.user != user:
            raise PermissionDenied("You can only update your own profile")

        super().perform_update(serializer)


class StudentProfileViewSet(AbstractViewSet):
    """
    ViewSet for StudentProfile model.

    Permissions:
    - Superadmin, Admin, Teacher: Full access to all student profiles
    - Student: Can view and update only their own profile
    """

    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filterset_class = StudentProfileFilterSet
    search_fields = [
        "user__first_name",
        "user__last_name",
        "grade_level",
        "roll_number",
    ]
    ordering_fields = ["id", "grade_level", "admission_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter student profiles based on user permissions."""
        queryset = super().get_queryset()

        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role in ["superadmin", "admin", "teacher"]:
            return queryset
        elif user.role == "student":
            return queryset.filter(user=user)

        return queryset.none()

    def perform_create(self, serializer):
        """Superadmin, Admin, and Teacher can create student profiles."""
        if self.request.user.role not in ["superadmin", "admin", "teacher"]:
            raise PermissionDenied(
                "Only superadmin, admin, and teacher can create student profiles"
            )

        super().perform_create(serializer)

    def perform_update(self, serializer):
        """Validate user can update student profile."""
        user = self.request.user
        instance = self.get_object()

        if user.role == "student" and instance.user != user:
            raise PermissionDenied("You can only update your own profile")

        super().perform_update(serializer)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated, IsTeacher],
    )
    def by_grade(self, request):
        """Get students by grade level. Teachers and above can access this."""
        try:
            grade = request.query_params.get("grade")
            if not grade:
                return self.error_response(message="Grade parameter is required")

            queryset = self.get_queryset().filter(grade_level=grade)
            serializer = self.get_serializer(queryset, many=True)

            return self.success_response(
                message=f"Students in grade '{grade}' retrieved successfully",
                data=serializer.data,
            )
        except Exception as e:
            return self.exception_response(e)


class TeacherProfileViewSet(AbstractViewSet):
    """
    ViewSet for TeacherProfile model.

    Permissions:
    - Superadmin & Admin: Full access to all teacher profiles
    - Teacher: Can view all teacher profiles, can update only their own
    """

    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filterset_class = TeacherProfileFilterSet
    search_fields = [
        "user__first_name",
        "user__last_name",
        "department",
        "subject_specialization",
        "employee_code",
    ]
    ordering_fields = ["id", "department", "hire_date", "experience_years"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter teacher profiles based on user permissions."""
        queryset = super().get_queryset()

        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role in ["superadmin", "admin"]:
            return queryset
        elif user.role == "teacher":
            return queryset.filter(user__role="teacher")

        return queryset.none()

    def perform_create(self, serializer):
        """Only superadmin and admin can create teacher profiles."""
        if self.request.user.role not in ["superadmin", "admin"]:
            raise PermissionDenied(
                "Only superadmin and admin can create teacher profiles"
            )

        super().perform_create(serializer)

    def perform_update(self, serializer):
        """Validate user can update teacher profile."""
        user = self.request.user
        instance = self.get_object()

        if user.role == "teacher" and instance.user != user:
            raise PermissionDenied("You can only update your own profile")

        super().perform_update(serializer)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated, IsTeacher],
    )
    def by_subject(self, request):
        """Get teachers by subject specialization. Teachers and above can access this."""
        try:
            subject = request.query_params.get("subject")
            if not subject:
                return self.error_response(message="Subject parameter is required")

            queryset = self.get_queryset().filter(
                subject_specialization__icontains=subject
            )
            serializer = self.get_serializer(queryset, many=True)

            return self.success_response(
                message=f"Teachers specializing in '{subject}' retrieved successfully",
                data=serializer.data,
            )
        except Exception as e:
            return self.exception_response(e)


class LogoutView(APIView, ResponseHandlerMixin):
    """Logout view that blacklists the refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Logout user by blacklisting the refresh token."""
        try:
            refresh_token = request.data.get("refresh_token")

            if not refresh_token:
                return self.error_response(
                    message="Refresh token is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return self.success_response(message="Successfully logged out")

        except TokenError:
            return self.error_response(
                message="Invalid or expired token",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return self.exception_response(e)


class SelfView(APIView, ResponseHandlerMixin):
    """View to retrieve the authenticated user's own information."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the authenticated user's information."""
        try:
            user = request.user
            serializer = Self(context={"request": request})
            data = serializer.to_representation(user)

            return self.success_response(
                message="User information retrieved successfully",
                data=data,
            )
        except Exception as e:
            return self.exception_response(e)
