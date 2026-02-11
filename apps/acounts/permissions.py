"""
Custom permission classes for role-based access control.

Place this file in: apps/acounts/permissions.py
"""

from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class to check if user is a superadmin.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "superadmin"
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission class to check if user is an admin or higher.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["superadmin", "admin"]
        )


class IsTeacher(permissions.BasePermission):
    """
    Permission class to check if user is a teacher or higher.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["superadmin", "admin", "teacher"]
        )


class IsStudent(permissions.BasePermission):
    """
    Permission class to check if user is a student.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "student"
        )


class IsBranchAdmin(permissions.BasePermission):
    """
    Permission class to check if user is a branch admin.
    Branch admin can only access data from their own branch.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
            and request.user.branch is not None
        )

    def has_object_permission(self, request, view, obj):
        """Check if the object belongs to the same branch as the admin"""
        if request.user.role == "superadmin":
            return True

        # For User objects
        if hasattr(obj, "branch"):
            return obj.branch == request.user.branch

        # For profile objects (StudentProfile, TeacherProfile, UserProfile)
        if hasattr(obj, "user") and hasattr(obj.user, "branch"):
            return obj.user.branch == request.user.branch

        return False
