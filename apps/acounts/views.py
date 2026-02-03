from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from apps.common.views import AbstractViewSet
from apps.acounts.models import User, UserProfile, StudentProfile, TeacherProfile
from apps.acounts.Serializers.account_serializers import (
    UserSerializer,
    UserProfileSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
)


class UserViewSet(AbstractViewSet):
    """
    ViewSet for User model with CRUD operations and role-based functionality.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on user role and permissions."""
        queryset = super().get_queryset()

        # Check if request exists (for schema generation)
        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return queryset

        # Superadmin can see all users
        if user.role == "superadmin":
            return queryset

        # Admin can see all except superadmin
        elif user.role == "admin":
            return queryset.exclude(role="superadmin")

        # Teachers can see students and other teachers
        elif user.role == "teacher":
            return queryset.filter(role__in=["student", "teacher"])

        # Students can only see themselves
        elif user.role == "student":
            return queryset.filter(id=user.id)

        return queryset.none()

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user's profile information."""
        try:
            serializer = self.get_serializer(request.user)
            return self.success_response(
                message="User profile retrieved successfully", data=serializer.data
            )
        except Exception as e:
            return self.exception_response(e)

    @action(detail=False, methods=["post"])
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

    @action(detail=False, methods=["get"])
    def by_role(self, request):
        """Get users filtered by role."""
        try:
            role = request.query_params.get("role")
            if not role:
                return self.error_response(message="Role parameter is required")

            queryset = self.get_queryset().filter(role=role)
            serializer = self.get_serializer(queryset, many=True)

            return self.success_response(
                message=f"Users with role '{role}' retrieved successfully",
                data=serializer.data,
            )
        except Exception as e:
            return self.exception_response(e)


class UserProfileViewSet(AbstractViewSet):
    """
    ViewSet for UserProfile model.
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter profiles based on user permissions."""
        queryset = super().get_queryset()

        # Check if request exists (for schema generation)
        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return queryset

        if user.role in ["superadmin", "admin"]:
            return queryset
        elif user.role == "teacher":
            # Teachers can see student profiles and their own
            return queryset.filter(user__role__in=["student", "teacher"])
        elif user.role == "student":
            # Students can only see their own profile
            return queryset.filter(user=user)

        return queryset.none()

    def perform_create(self, serializer):
        """Set created_by when creating profile."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set updated_by when updating profile."""
        serializer.save(updated_by=self.request.user)


class StudentProfileViewSet(AbstractViewSet):
    """
    ViewSet for StudentProfile model.
    """

    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter student profiles based on user permissions."""
        queryset = super().get_queryset()

        # Check if request exists (for schema generation)
        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return queryset

        if user.role in ["superadmin", "admin", "teacher"]:
            return queryset
        elif user.role == "student":
            # Students can only see their own profile
            return queryset.filter(user=user)

        return queryset.none()

    def perform_create(self, serializer):
        """Set created_by when creating student profile."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set updated_by when updating student profile."""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"])
    def by_grade(self, request):
        """Get students by grade level."""
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
    """

    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter teacher profiles based on user permissions."""
        queryset = super().get_queryset()

        # Check if request exists (for schema generation)
        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return queryset

        if user.role in ["superadmin", "admin"]:
            return queryset
        elif user.role == "teacher":
            # Teachers can see their own profile and other teachers
            return queryset.filter(user__role="teacher")

        return queryset.none()

    def perform_create(self, serializer):
        """Set created_by when creating teacher profile."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set updated_by when updating teacher profile."""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"])
    def by_department(self, request):
        """Get teachers by department."""
        try:
            department = request.query_params.get("department")
            if not department:
                return self.error_response(message="Department parameter is required")

            queryset = self.get_queryset().filter(department=department)
            serializer = self.get_serializer(queryset, many=True)

            return self.success_response(
                message=f"Teachers in '{department}' department retrieved successfully",
                data=serializer.data,
            )
        except Exception as e:
            return self.exception_response(e)

    @action(detail=False, methods=["get"])
    def by_subject(self, request):
        """Get teachers by subject specialization."""
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


class LogoutView(APIView):
    """
    Logout view that blacklists the refresh token.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Logout user by blacklisting the refresh token.
        """
        try:
            refresh_token = request.data.get("refresh_token")

            if not refresh_token:
                return Response(
                    {
                        "success": False,
                        "message": "Refresh token is required",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create RefreshToken instance and blacklist it
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"success": True, "message": "Successfully logged out", "data": None},
                status=status.HTTP_200_OK,
            )

        except TokenError as e:
            return Response(
                {
                    "success": False,
                    "message": "Invalid or expired token",
                    "data": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"An error occurred: {str(e)}",
                    "data": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
