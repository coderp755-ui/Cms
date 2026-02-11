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
    BranchSerializer,
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
from apps.acounts.models import Branch


class BranchViewSet(AbstractViewSet):
    """
    ViewSet for Branch model with CRUD operations.

    Permissions:
    - Superadmin: Full access - can add/edit/delete all branches
    - Admin: Can view branches only
    - Teacher & Student: Can view branches only
    """

    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomDefaultPagination
    search_fields = ["name", "code", "address", "phone", "email"]
    ordering_fields = ["id", "name", "code", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        """Filter branches based on user role."""
        queryset = super().get_queryset()

        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()

        # Superadmin can see all branches
        if user.role == "superadmin":
            return queryset

        # Admin, Teacher, Student can see active branches
        return queryset.filter(is_active=True)

    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ["list", "retrieve"]:
            # All authenticated users can view branches
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Only superadmin can create/update/delete branches
            permission_classes = [permissions.IsAuthenticated, IsAdmin]

        return [permission() for permission in permission_classes]


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
        """Filter queryset based on user role and permissions with branch filtering."""
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
        # Branch Admin can only see users from their branch
        elif user.role == "admin":
            if user.branch:
                # Branch admin can only see users from their branch
                return queryset.filter(branch=user.branch)
            else:
                # Admin without branch can see all (backward compatibility)
                return queryset
        # Teachers can see students and teachers from their branch only
        elif user.role == "teacher":
            if user.branch:
                return queryset.filter(
                    role__in=["student", "teacher"], branch=user.branch
                )
            else:
                return queryset.filter(role__in=["student", "teacher"])
        # Students can only see themselves
        elif user.role == "student":
            return queryset.filter(id=user.id)

        return queryset.none()

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def enroll_courses(self, request, pk=None):
        """Enroll a student in courses. Admin and Teacher can enroll students."""
        try:
            user = self.get_object()

            if user.role != "student":
                return self.error_response(
                    message="Only students can be enrolled in courses",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Check permission - only admin and teacher can enroll
            if request.user.role not in ["superadmin", "admin", "teacher"]:
                return self.error_response(
                    message="You don't have permission to enroll students",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            # Teacher can only enroll students from their branch
            if request.user.role == "teacher":
                if request.user.branch != user.branch:
                    return self.error_response(
                        message="You can only enroll students from your branch",
                        status_code=status.HTTP_403_FORBIDDEN,
                    )

            course_ids = request.data.get("course_ids", [])
            if not course_ids:
                return self.error_response(
                    message="course_ids is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            from apps.classes.models import Course

            # Validate courses exist and belong to the same branch
            courses = Course.objects.filter(
                id__in=course_ids, is_active=True, is_deleted=False
            )

            if not courses.exists():
                return self.error_response(
                    message="No valid courses found",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Check if courses belong to user's branch
            if user.branch:
                invalid_courses = courses.exclude(branch=user.branch)
                if invalid_courses.exists():
                    return self.error_response(
                        message="Some courses do not belong to the student's branch",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

            # Enroll student in courses
            user.enrolled_courses.set(courses)

            return self.success_response(
                message=f"Student enrolled in {courses.count()} course(s) successfully",
                data={
                    "enrolled_courses": [
                        {"id": c.id, "title": c.title, "course_type": c.course_type}
                        for c in courses
                    ]
                },
            )
        except Exception as e:
            return self.exception_response(e)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def unenroll_courses(self, request, pk=None):
        """Unenroll a student from courses. Admin and Teacher can unenroll students."""
        try:
            user = self.get_object()

            if user.role != "student":
                return self.error_response(
                    message="Only students can be unenrolled from courses",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Check permission - only admin and teacher can unenroll
            if request.user.role not in ["superadmin", "admin", "teacher"]:
                return self.error_response(
                    message="You don't have permission to unenroll students",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            # Teacher can only unenroll students from their branch
            if request.user.role == "teacher":
                if request.user.branch != user.branch:
                    return self.error_response(
                        message="You can only unenroll students from your branch",
                        status_code=status.HTTP_403_FORBIDDEN,
                    )

            course_ids = request.data.get("course_ids", [])
            if not course_ids:
                return self.error_response(
                    message="course_ids is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            from apps.classes.models import Course

            # Remove courses from enrollment
            courses = Course.objects.filter(id__in=course_ids)
            user.enrolled_courses.remove(*courses)

            return self.success_response(
                message=f"Student unenrolled from {courses.count()} course(s) successfully"
            )
        except Exception as e:
            return self.exception_response(e)

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
            user.must_change_password = False  # Mark password as changed
            user.save()

            return self.success_response(message="Password changed successfully")
        except Exception as e:
            return self.exception_response(e)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def force_change_password(self, request):
        """Force change password on first login (no old password required)."""
        try:
            new_password = request.data.get("new_password")
            confirm_password = request.data.get("confirm_password")

            if not new_password or not confirm_password:
                return self.error_response(
                    message="Both new_password and confirm_password are required"
                )

            if new_password != confirm_password:
                return self.error_response(message="Passwords do not match")

            user = request.user

            # Only allow if user must change password
            if not user.must_change_password:
                return self.error_response(
                    message="You are not required to change your password. Use change_password endpoint instead.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(new_password)
            user.must_change_password = False
            user.save()

            return self.success_response(
                message="Password changed successfully. You can now login with your new password."
            )
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
        """Filter profiles based on user permissions with branch filtering."""
        queryset = super().get_queryset()

        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role == "superadmin":
            return queryset
        elif user.role == "admin":
            if user.branch:
                # Branch admin can only see profiles from their branch
                return queryset.filter(user__branch=user.branch)
            else:
                return queryset
        elif user.role == "teacher":
            if user.branch:
                return queryset.filter(
                    user__role__in=["student", "teacher"], user__branch=user.branch
                )
            else:
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

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def create_own_profile(self, request):
        """Allow any user to create their own basic profile."""
        try:
            user = request.user

            # Check if profile already exists
            if UserProfile.objects.filter(user=user).exists():
                return self.error_response(
                    message="Your user profile already exists",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Serializer will automatically use request.user.id from context
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=user)

            return self.success_response(
                message="User profile created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.exception_response(e)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def my_profile(self, request):
        """Get the authenticated user's own profile."""
        try:
            user = request.user

            try:
                profile = UserProfile.objects.get(user=user)
                serializer = self.get_serializer(profile)
                return self.success_response(
                    message="User profile retrieved successfully",
                    data=serializer.data,
                )
            except UserProfile.DoesNotExist:
                return self.error_response(
                    message="Your user profile has not been created yet. Please create your profile.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            return self.exception_response(e)


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
        """Filter student profiles based on user permissions with branch filtering."""
        queryset = super().get_queryset()

        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role == "superadmin":
            return queryset
        elif user.role == "admin":
            if user.branch:
                # Branch admin can only see students from their branch
                return queryset.filter(user__branch=user.branch)
            else:
                return queryset
        elif user.role == "teacher":
            if user.branch:
                return queryset.filter(user__branch=user.branch)
            else:
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

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def create_own_profile(self, request):
        """Allow students to create their own profile."""
        try:
            user = request.user

            # Only students can use this endpoint
            if user.role != "student":
                return self.error_response(
                    message="This endpoint is only for students",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            # Check if profile already exists
            if StudentProfile.objects.filter(user=user).exists():
                return self.error_response(
                    message="Your student profile already exists",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Serializer will automatically use request.user.id from context
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create_own(serializer)

            return self.success_response(
                message="Student profile created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.exception_response(e)

    def perform_create_own(self, serializer):
        """Save the student profile without permission check."""
        serializer.save(created_by=self.request.user)

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
        permission_classes=[permissions.IsAuthenticated],
    )
    def my_profile(self, request):
        """Get the authenticated student's own profile."""
        try:
            user = request.user

            if user.role != "student":
                return self.error_response(
                    message="This endpoint is only for students",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            try:
                profile = StudentProfile.objects.get(user=user)
                serializer = self.get_serializer(profile)
                return self.success_response(
                    message="Student profile retrieved successfully",
                    data=serializer.data,
                )
            except StudentProfile.DoesNotExist:
                return self.error_response(
                    message="Your student profile has not been created yet. Please create your profile.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            return self.exception_response(e)

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
        """Filter teacher profiles based on user permissions with branch filtering."""
        queryset = super().get_queryset()

        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role == "superadmin":
            return queryset
        elif user.role == "admin":
            if user.branch:
                # Branch admin can only see teachers from their branch
                return queryset.filter(user__branch=user.branch)
            else:
                return queryset
        elif user.role == "teacher":
            if user.branch:
                return queryset.filter(user__role="teacher", user__branch=user.branch)
            else:
                return queryset.filter(user__role="teacher")

        return queryset.none()

    def perform_create(self, serializer):
        """Only superadmin and admin can create teacher profiles."""
        if self.request.user.role not in ["superadmin", "admin"]:
            raise PermissionDenied(
                "Only superadmin and admin can create teacher profiles"
            )

        super().perform_create(serializer)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def create_own_profile(self, request):
        """Allow teachers to create their own profile."""
        try:
            user = request.user

            # Only teachers can use this endpoint
            if user.role != "teacher":
                return self.error_response(
                    message="This endpoint is only for teachers",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            # Check if profile already exists
            if TeacherProfile.objects.filter(user=user).exists():
                return self.error_response(
                    message="Your teacher profile already exists",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Serializer will automatically use request.user.id from context
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create_own(serializer)

            return self.success_response(
                message="Teacher profile created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.exception_response(e)

    def perform_create_own(self, serializer):
        """Save the teacher profile without permission check."""
        serializer.save(created_by=self.request.user)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def my_profile(self, request):
        """Get the authenticated teacher's own profile."""
        try:
            user = request.user

            if user.role != "teacher":
                return self.error_response(
                    message="This endpoint is only for teachers",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            try:
                profile = TeacherProfile.objects.get(user=user)
                serializer = self.get_serializer(profile)
                return self.success_response(
                    message="Teacher profile retrieved successfully",
                    data=serializer.data,
                )
            except TeacherProfile.DoesNotExist:
                return self.error_response(
                    message="Your teacher profile has not been created yet. Please create your profile.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            return self.exception_response(e)

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


class ForgotPasswordRequestView(APIView, ResponseHandlerMixin):
    """Request OTP for password reset via email."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Send OTP to user's email for password reset."""
        try:
            email = request.data.get("email")

            if not email:
                return self.error_response(
                    message="Email is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                user = User.objects.get(email=email, is_active=True)
            except User.DoesNotExist:
                return self.error_response(
                    message="No active user found with this email",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            # Generate OTP
            otp = user.generate_otp()

            # Send OTP via email
            from django.core.mail import send_mail
            from django.conf import settings

            try:
                send_mail(
                    subject="Password Reset OTP",
                    message=f"Your OTP for password reset is: {otp}\n\nThis OTP is valid for 10 minutes.\n\nIf you did not request this, please ignore this email.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                return self.success_response(
                    message=f"OTP sent successfully to {email}. Please check your email.",
                    data={"email": email},
                )
            except Exception as e:
                return self.error_response(
                    message=f"Failed to send email: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            return self.exception_response(e)


class ForgotPasswordVerifyView(APIView, ResponseHandlerMixin):
    """Verify OTP and reset password."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Verify OTP and reset password."""
        try:
            email = request.data.get("email")
            otp = request.data.get("otp")
            new_password = request.data.get("new_password")
            confirm_password = request.data.get("confirm_password")

            if not all([email, otp, new_password, confirm_password]):
                return self.error_response(
                    message="Email, OTP, new_password, and confirm_password are required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            if new_password != confirm_password:
                return self.error_response(
                    message="Passwords do not match",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                user = User.objects.get(email=email, is_active=True)
            except User.DoesNotExist:
                return self.error_response(
                    message="No active user found with this email",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            # Verify OTP
            if not user.verify_otp(otp):
                return self.error_response(
                    message="Invalid or expired OTP",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Reset password
            user.set_password(new_password)
            user.must_change_password = False
            user.clear_otp()

            return self.success_response(
                message="Password reset successfully. You can now login with your new password."
            )
        except Exception as e:
            return self.exception_response(e)
