from rest_framework import permissions
from apps.common.views import AbstractViewSet
from apps.common.paginations.default_paginations import CustomDefaultPagination
from apps.classes.Serializers.CourseSerializers import CourseSerializer
from apps.classes.Serializers.SectionSerializer import SectionSerializer
from apps.classes.Serializers.LessonSerializers import LessonSerializer
from apps.classes.Serializers.LessonProgressSerializers import LessonProgressSerializer
from apps.classes.models import Course, Section, Lesson, LessonProgress
from apps.acounts.permissions import (
    IsSuperAdmin,
    IsAdmin,
    IsTeacher,
)


class CourseViewSet(AbstractViewSet):
    """
    Course ViewSet with role-based permissions and branch filtering.

    Permissions:
    - Create/Update/Delete: Superadmin, Admin, Teacher only
    - View (List/Retrieve): All authenticated users (including Students)
    
    Branch Filtering:
    - Superadmin: Can see all courses
    - Branch Admin: Can only see courses from their branch
    - Teacher: Can only see courses from their branch
    - Student: Can only see courses from their branch
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = CustomDefaultPagination

    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ["list", "retrieve"]:
            # Anyone authenticated can view courses
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Only superadmin, admin, teacher can create/update/delete
            permission_classes = [IsTeacher, IsSuperAdmin, IsAdmin]

        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter courses based on user's branch and enrollment."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # Superadmin can see all courses
        if user.role == "superadmin":
            return queryset
        
        # Students can only see their enrolled courses
        if user.role == "student":
            if user.enrolled_courses.exists():
                return queryset.filter(id__in=user.enrolled_courses.values_list('id', flat=True))
            else:
                # If no enrolled courses, show courses from their branch
                if user.branch:
                    return queryset.filter(branch=user.branch)
                return queryset.none()
        
        # Branch-based filtering for admin and teacher
        if user.branch:
            return queryset.filter(branch=user.branch)
        
        # If user has no branch, return all courses (backward compatibility)
        return queryset


class SectionViewSet(AbstractViewSet):
    """
    Section ViewSet with role-based permissions and branch filtering.

    Permissions:
    - Create/Update/Delete: Superadmin, Admin, Teacher only
    - View (List/Retrieve): All authenticated users (including Students)
    
    Branch Filtering:
    - Sections are filtered based on their course's branch
    """

    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    pagination_class = CustomDefaultPagination

    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ["list", "retrieve"]:
            # Anyone authenticated can view sections
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Only superadmin, admin, teacher can create/update/delete
            permission_classes = [IsTeacher, IsSuperAdmin, IsAdmin]

        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter sections based on user's branch and enrolled courses."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # Superadmin can see all sections
        if user.role == "superadmin":
            return queryset
        
        # Students can only see sections from their enrolled courses
        if user.role == "student":
            if user.enrolled_courses.exists():
                return queryset.filter(course__id__in=user.enrolled_courses.values_list('id', flat=True))
            else:
                # If no enrolled courses, show sections from their branch courses
                if user.branch:
                    return queryset.filter(course__branch=user.branch)
                return queryset.none()
        
        # Branch-based filtering through course for admin and teacher
        if user.branch:
            return queryset.filter(course__branch=user.branch)
        
        # If user has no branch, return all sections (backward compatibility)
        return queryset


class LessonViewSet(AbstractViewSet):
    """
    Lesson ViewSet with role-based permissions and branch filtering.

    Permissions:
    - Create/Update/Delete: Superadmin, Admin, Teacher only
    - View (List/Retrieve): All authenticated users (including Students)
    
    Branch Filtering:
    - Lessons are filtered based on their section's course's branch
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = CustomDefaultPagination

    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ["list", "retrieve"]:
            # Anyone authenticated can view lessons
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Only superadmin, admin, teacher can create/update/delete
            permission_classes = [IsTeacher, IsSuperAdmin, IsAdmin]

        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter lessons based on user's branch and enrolled courses."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # Superadmin can see all lessons
        if user.role == "superadmin":
            return queryset
        
        # Students can only see lessons from their enrolled courses
        if user.role == "student":
            if user.enrolled_courses.exists():
                return queryset.filter(section__course__id__in=user.enrolled_courses.values_list('id', flat=True))
            else:
                # If no enrolled courses, show lessons from their branch courses
                if user.branch:
                    return queryset.filter(section__course__branch=user.branch)
                return queryset.none()
        
        # Branch-based filtering through section and course for admin and teacher
        if user.branch:
            return queryset.filter(section__course__branch=user.branch)
        
        # If user has no branch, return all lessons (backward compatibility)
        return queryset



class LessonProgressViewSet(AbstractViewSet):
    """
    LessonProgress ViewSet to track user's lesson reading progress.

    Permissions:
    - Create/Update: All authenticated users (students track their own progress)
    - View (List/Retrieve): All authenticated users
    - Delete: Superadmin, Admin only
    """

    queryset = LessonProgress.objects.all()
    serializer_class = LessonProgressSerializer
    pagination_class = CustomDefaultPagination

    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ["list", "retrieve", "create", "update", "partial_update"]:
            # All authenticated users can view and update their progress
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Only superadmin, admin can delete
            permission_classes = [IsSuperAdmin, IsAdmin]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter progress by current user if not admin, with branch filtering."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # Superadmin can see all progress
        if user.role == "superadmin":
            return queryset
        
        # Branch admin can see progress of users in their branch
        if user.role == "admin" and user.branch:
            return queryset.filter(user__branch=user.branch)
        
        # Teachers can see progress of students in their branch
        if user.role == "teacher" and user.branch:
            return queryset.filter(user__branch=user.branch, user__role="student")
        
        # Students can only see their own progress
        return queryset.filter(user=user)
