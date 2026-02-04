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
        return request.user and request.user.is_authenticated and request.user.role == 'superadmin'


class IsAdmin(permissions.BasePermission):
    """
    Permission class to check if user is an admin or higher.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['superadmin', 'admin']


class IsTeacher(permissions.BasePermission):
    """
    Permission class to check if user is a teacher or higher.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['superadmin', 'admin', 'teacher']


class IsStudent(permissions.BasePermission):
    """
    Permission class to check if user is a student.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'student'


class RoleBasedPermission(permissions.BasePermission):
    """
    Advanced role-based permission class with action-level control.
    
    Usage in ViewSet:
        permission_classes = [RoleBasedPermission]
        
        # Define role permissions in the viewset
        role_permissions = {
            'superadmin': ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'],
            'admin': ['list', 'retrieve', 'create', 'update', 'partial_update'],
            'teacher': ['list', 'retrieve'],
            'student': ['retrieve'],
        }
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get the action being performed
        action = view.action if hasattr(view, 'action') else None
        
        # Get role permissions from viewset
        role_permissions = getattr(view, 'role_permissions', {})
        
        # If no role_permissions defined, deny access
        if not role_permissions:
            return False
        
        # Get user's role
        user_role = request.user.role
        
        # Check if user's role has permission for this action
        allowed_actions = role_permissions.get(user_role, [])
        
        return action in allowed_actions
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_role = request.user.role
        action = view.action if hasattr(view, 'action') else None
        
        # Superadmin can access everything
        if user_role == 'superadmin':
            return True
        
        # Admin cannot modify superadmin accounts
        if user_role == 'admin':
            if hasattr(obj, 'role') and obj.role == 'superadmin':
                return False
            if hasattr(obj, 'user') and obj.user.role == 'superadmin':
                return False
            return True
        
        # Teacher can only view, not modify
        if user_role == 'teacher':
            return action in ['retrieve', 'list']
        
        # Student can only access their own data
        if user_role == 'student':
            if hasattr(obj, 'user'):
                return obj.user == request.user
            return obj == request.user
        
        return False


class UserManagementPermission(permissions.BasePermission):
    """
    Permission for User management with hierarchy control.
    
    Hierarchy:
    - Superadmin: Can manage all roles
    - Admin: Can manage teachers and students (not superadmin)
    - Teacher: Can view students and teachers, but cannot create/update/delete
    - Student: Can only view/update their own profile
    """
    
    def has_permission(self, request, view):
        """Check if user can perform the action."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_role = request.user.role
        action = view.action if hasattr(view, 'action') else None
        
        # Define permissions per role
        permissions_map = {
            'superadmin': ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'],
            'admin': ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'],
            'teacher': ['list', 'retrieve'],
            'student': ['retrieve', 'update', 'partial_update'],
        }
        
        allowed_actions = permissions_map.get(user_role, [])
        return action in allowed_actions
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access/modify specific user object."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_role = request.user.role
        action = view.action if hasattr(view, 'action') else None
        
        # Get target user (handle both User objects and Profile objects)
        target_user = obj if hasattr(obj, 'role') else getattr(obj, 'user', None)
        
        if not target_user:
            return False
        
        # Superadmin can do anything
        if user_role == 'superadmin':
            return True
        
        # Admin cannot manage superadmins
        if user_role == 'admin':
            if target_user.role == 'superadmin':
                return False
            # Admin can manage teachers and students
            return target_user.role in ['admin', 'teacher', 'student']
        
        # Teacher can only view (not modify)
        if user_role == 'teacher':
            if action in ['retrieve', 'list']:
                return target_user.role in ['teacher', 'student']
            return False
        
        # Student can only access their own data
        if user_role == 'student':
            return target_user.id == request.user.id
        
        return False


class ProfilePermission(permissions.BasePermission):
    """
    Permission for Profile management (UserProfile, StudentProfile, TeacherProfile).
    
    Rules:
    - Superadmin & Admin: Full access to all profiles
    - Teacher: Can view student and teacher profiles, can update own profile
    - Student: Can view and update only their own profile
    """
    
    def has_permission(self, request, view):
        """Check if user can perform the action."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_role = request.user.role
        action = view.action if hasattr(view, 'action') else None
        
        # Superadmin and Admin have full access
        if user_role in ['superadmin', 'admin']:
            return True
        
        # Teacher can list, retrieve, and update
        if user_role == 'teacher':
            return action in ['list', 'retrieve', 'update', 'partial_update']
        
        # Student can retrieve and update
        if user_role == 'student':
            return action in ['retrieve', 'update', 'partial_update']
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access/modify specific profile object."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_role = request.user.role
        action = view.action if hasattr(view, 'action') else None
        
        # Superadmin and Admin can access all profiles
        if user_role in ['superadmin', 'admin']:
            return True
        
        # Teacher can view all student/teacher profiles, but only update their own
        if user_role == 'teacher':
            if action in ['retrieve', 'list']:
                return obj.user.role in ['teacher', 'student']
            elif action in ['update', 'partial_update']:
                return obj.user.id == request.user.id
            return False
        
        # Student can only access their own profile
        if user_role == 'student':
            return obj.user.id == request.user.id
        
        return False


class CanCreateUser(permissions.BasePermission):
    """
    Permission to check if user can create another user based on role hierarchy.
    
    Rules:
    - Superadmin: Can create superadmin, admin, teacher, student
    - Admin: Can create admin, teacher, student (not superadmin)
    - Teacher: Cannot create users
    - Student: Cannot create users
    """
    
    def has_permission(self, request, view):
        """Check if user can create a new user."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only check for create action
        action = view.action if hasattr(view, 'action') else None
        if action != 'create':
            return True  # Let other permissions handle non-create actions
        
        user_role = request.user.role
        
        # Only superadmin and admin can create users
        if user_role in ['superadmin', 'admin']:
            # Check the role of the user being created
            target_role = request.data.get('role')
            
            if user_role == 'superadmin':
                # Superadmin can create any role
                return True
            elif user_role == 'admin':
                # Admin cannot create superadmin
                return target_role != 'superadmin'
        
        return False


class CanDeleteUser(permissions.BasePermission):
    """
    Permission to check if user can delete another user based on role hierarchy.
    
    Rules:
    - Superadmin: Can delete any user
    - Admin: Can delete teacher and student (not superadmin or admin)
    - Teacher: Cannot delete users
    - Student: Cannot delete users
    """
    
    def has_permission(self, request, view):
        """Check if user can delete users."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        action = view.action if hasattr(view, 'action') else None
        if action != 'destroy':
            return True  # Let other permissions handle non-delete actions
        
        user_role = request.user.role
        
        # Only superadmin and admin can delete users
        return user_role in ['superadmin', 'admin']
    
    def has_object_permission(self, request, view, obj):
        """Check if user can delete specific user object."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_role = request.user.role
        target_user = obj if hasattr(obj, 'role') else getattr(obj, 'user', None)
        
        if not target_user:
            return False
        
        # Superadmin can delete anyone
        if user_role == 'superadmin':
            return True
        
        # Admin can delete teacher and student only
        if user_role == 'admin':
            return target_user.role in ['teacher', 'student']
        
        return False


# Convenience permission combinations
class SuperAdminOrReadOnly(permissions.BasePermission):
    """Only superadmin can modify, others can read."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.role == 'superadmin'


class AdminOrReadOnly(permissions.BasePermission):
    """Admin and above can modify, others can read."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.role in ['superadmin', 'admin']