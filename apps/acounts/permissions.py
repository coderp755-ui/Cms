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
