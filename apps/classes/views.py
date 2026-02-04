from rest_framework import permissions
from apps.common.views import AbstractViewSet
from apps.classes.Serializers.CourseSerializers import CourseSerializer
from apps.classes.Serializers.SectionSerializer import SectionSerializer
from apps.classes.Serializers.LessonSerializers import LessonSerializer
from apps.classes.models import Course, Section, Lesson
from apps.acounts.permissions import (
    IsSuperAdmin,
    IsAdmin,
    IsTeacher,
)


class CourseViewSet(AbstractViewSet):
    """
    Course ViewSet with role-based permissions.

    Permissions:
    - Create/Update/Delete: Superadmin, Admin, Teacher only
    - View (List/Retrieve): All authenticated users (including Students)
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ["list", "retrieve"]:
            # Anyone authenticated can view courses
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Only superadmin, admin, teacher can create/update/delete
            permission_classes = [IsTeacher,IsSuperAdmin,IsAdmin]

        return [permission() for permission in permission_classes]


class SectionViewSet(AbstractViewSet):
    """
    Section ViewSet with role-based permissions.

    Permissions:
    - Create/Update/Delete: Superadmin, Admin, Teacher only
    - View (List/Retrieve): All authenticated users (including Students)
    """

    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ["list", "retrieve"]:
            # Anyone authenticated can view sections
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Only superadmin, admin, teacher can create/update/delete
            permission_classes = [IsTeacher,IsSuperAdmin,IsAdmin]

        return [permission() for permission in permission_classes]


class LessonViewSet(AbstractViewSet):
    """
    Lesson ViewSet with role-based permissions.

    Permissions:
    - Create/Update/Delete: Superadmin, Admin, Teacher only
    - View (List/Retrieve): All authenticated users (including Students)
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        """Apply different permissions based on action."""
        if self.action in ["list", "retrieve"]:
            # Anyone authenticated can view lessons
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Only superadmin, admin, teacher can create/update/delete
           permission_classes = [IsTeacher,IsSuperAdmin,IsAdmin]

        return [permission() for permission in permission_classes]
