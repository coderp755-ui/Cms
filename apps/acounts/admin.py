from django.contrib import admin
from apps.acounts.models import (
    Branch,
    User,
    UserProfile,
    StudentProfile,
    TeacherProfile,
)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'phone', 'email']
    ordering = ['name']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'branch', 'employee_id', 'student_id', 'is_active']
    list_filter = ['role', 'branch', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id', 'student_id']
    ordering = ['-date_joined']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'is_active_profile']
    list_filter = ['is_active_profile']
    search_fields = ['user__username', 'phone_number']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'grade_level', 'roll_number', 'admission_date']
    list_filter = ['grade_level', 'admission_date']
    search_fields = ['user__username', 'roll_number', 'user__student_id']


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'subject_specialization', 'hire_date']
    list_filter = ['department', 'employment_type', 'hire_date']
    search_fields = ['user__username', 'employee_code', 'department', 'subject_specialization']

