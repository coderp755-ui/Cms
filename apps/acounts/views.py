"""
Updated views.py with role-based permissions.

This file includes:
- Custom permission classes applied to each ViewSet
- Role hierarchy enforcement
- Object-level permissions
"""
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from apps.common.views import AbstractViewSet
from apps.acounts.models import User, UserProfile, StudentProfile, TeacherProfile
from apps.acounts.Serializers.account_serializers import (
    Self,
    UserSerializer,
    UserProfileSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
)
from apps.acounts.permissions import (
    UserManagementPermission,
    ProfilePermission,
    CanCreateUser,
    CanDeleteUser,
    IsSuperAdmin,
    IsAdmin,
)


class UserViewSet(AbstractViewSet):
    """
    ViewSet for User model with CRUD operations and role-based functionality.
    
    Permissions:
    - Superadmin: Full access to all users
    - Admin: Can manage teachers and students (cannot manage superadmins)
    - Teacher: Can view students and teachers only
    - Student: Can view and update only their own profile
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        Apply different permissions based on action.
        """
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, CanCreateUser]
        elif self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated, CanDeleteUser]
        else:
            permission_classes = [permissions.IsAuthenticated, UserManagementPermission]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user role and permissions."""
        queryset = super().get_queryset()

        # Check if request exists (for schema generation)
        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return queryset.none()

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
    
    def perform_create(self, serializer):
        """
        Validate role hierarchy when creating user.
        Prevent admin from creating superadmin.
        """
        user = self.request.user
        target_role = self.request.data.get('role')
        
        # Admin cannot create superadmin
        if user.role == 'admin' and target_role == 'superadmin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admins cannot create superadmin users")
        
        serializer.save(created_by=user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating user."""
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """
        Validate role hierarchy when deleting user.
        Use soft delete from BaseModel.
        """
        user = self.request.user
        
        # Prevent admin from deleting superadmin or other admins
        if user.role == 'admin' and instance.role in ['superadmin', 'admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(f"Admins cannot delete {instance.role} users")
        
        # Prevent users from deleting themselves
        if instance.id == user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You cannot delete your own account")
        
        # Soft delete instead of hard delete
        instance.soft_delete()

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
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

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def by_role(self, request):
        """
        Get users filtered by role.
        Only superadmin and admin can use this endpoint.
        """
        try:
            # Check permission
            if request.user.role not in ['superadmin', 'admin']:
                return self.error_response(
                    message="You don't have permission to filter users by role",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            role = request.query_params.get("role")
            if not role:
                return self.error_response(message="Role parameter is required")

            # Admin cannot query superadmin users
            if request.user.role == 'admin' and role == 'superadmin':
                return self.error_response(
                    message="You don't have permission to view superadmin users",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            queryset = self.get_queryset().filter(role=role)
            serializer = self.get_serializer(queryset, many=True)

            return self.success_response(
                message=f"Users with role '{role}' retrieved successfully",
                data=serializer.data,
            )
        except Exception as e:
            return self.exception_response(e)
    
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsAdmin])
    def activate(self, request, pk=None):
        """
        Activate a user account.
        Only superadmin and admin can activate users.
        """
        try:
            user = self.get_object()
            
            # Admin cannot activate superadmin
            if request.user.role == 'admin' and user.role == 'superadmin':
                return self.error_response(
                    message="You don't have permission to activate superadmin users",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            user.is_active = True
            user.save()
            
            return self.success_response(message=f"User {user.username} activated successfully")
        except Exception as e:
            return self.exception_response(e)
    
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsAdmin])
    def deactivate(self, request, pk=None):
        """
        Deactivate a user account.
        Only superadmin and admin can deactivate users.
        """
        try:
            user = self.get_object()
            
            # Admin cannot deactivate superadmin
            if request.user.role == 'admin' and user.role == 'superadmin':
                return self.error_response(
                    message="You don't have permission to deactivate superadmin users",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            # Prevent users from deactivating themselves
            if user.id == request.user.id:
                return self.error_response(
                    message="You cannot deactivate your own account",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            user.is_active = False
            user.save()
            
            return self.success_response(message=f"User {user.username} deactivated successfully")
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
    permission_classes = [permissions.IsAuthenticated, ProfilePermission]

    def get_queryset(self):
        """Filter profiles based on user permissions."""
        queryset = super().get_queryset()

        # Check if request exists (for schema generation)
        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return queryset.none()

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
    
    Permissions:
    - Superadmin, Admin, Teacher: Full access to all student profiles
    - Student: Can view and update only their own profile
    """

    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, ProfilePermission]

    def get_queryset(self):
        """Filter student profiles based on user permissions."""
        queryset = super().get_queryset()

        # Check if request exists (for schema generation)
        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role in ["superadmin", "admin", "teacher"]:
            return queryset
        elif user.role == "student":
            # Students can only see their own profile
            return queryset.filter(user=user)

        return queryset.none()

    def perform_create(self, serializer):
        """Set created_by when creating student profile."""
        # Only superadmin and admin can create student profiles
        if self.request.user.role not in ['superadmin', 'admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only superadmin and admin can create student profiles")
        
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set updated_by when updating student profile."""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def by_grade(self, request):
        """
        Get students by grade level.
        Teachers and above can access this.
        """
        try:
            # Check permission
            if request.user.role not in ['superadmin', 'admin', 'teacher']:
                return self.error_response(
                    message="You don't have permission to filter students by grade",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
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
    permission_classes = [permissions.IsAuthenticated, ProfilePermission]

    def get_queryset(self):
        """Filter teacher profiles based on user permissions."""
        queryset = super().get_queryset()

        # Check if request exists (for schema generation)
        if not hasattr(self, "request") or not self.request:
            return queryset

        user = self.request.user

        # Check if user is authenticated
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role in ["superadmin", "admin"]:
            return queryset
        elif user.role == "teacher":
            # Teachers can see their own profile and other teachers
            return queryset.filter(user__role="teacher")

        return queryset.none()

    def perform_create(self, serializer):
        """Set created_by when creating teacher profile."""
        # Only superadmin and admin can create teacher profiles
        if self.request.user.role not in ['superadmin', 'admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only superadmin and admin can create teacher profiles")
        
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set updated_by when updating teacher profile."""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def by_department(self, request):
        """
        Get teachers by department.
        Superadmin and admin can access this.
        """
        try:
            # Check permission
            if request.user.role not in ['superadmin', 'admin']:
                return self.error_response(
                    message="You don't have permission to filter teachers by department",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
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

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def by_subject(self, request):
        """
        Get teachers by subject specialization.
        Teachers and above can access this.
        """
        try:
            # Check permission
            if request.user.role not in ['superadmin', 'admin', 'teacher']:
                return self.error_response(
                    message="You don't have permission to filter teachers by subject",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
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

    
class SelfView(APIView):
    """
    View to retrieve the authenticated user's own information.
    Any authenticated user can access their own information.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Retrieve the authenticated user's information.
        """
        try:
            user = request.user
            serializer = Self(context={"request": request})
            data = serializer.to_representation(user)

            return Response(
                {
                    "success": True,
                    "message": "User information retrieved successfully",
                    "data": data,
                },
                status=status.HTTP_200_OK,
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