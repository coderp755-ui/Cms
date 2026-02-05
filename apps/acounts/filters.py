"""
Filters for User and Profile models.
"""
from django_filters import rest_framework as filters
from apps.acounts.models import User, StudentProfile, TeacherProfile


class UserFilterSet(filters.FilterSet):
    """
    FilterSet for User model with search and filter capabilities.
    """
    # Role filter
    role = filters.ChoiceFilter(
        choices=User.ROLE_CHOICES,
        help_text="Filter by user role (superadmin, admin, teacher, student)"
    )
    
    # ID filters
    employee_id = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by employee ID (partial match)"
    )
    student_id = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by student ID (partial match)"
    )
    
    # Name filters
    name = filters.CharFilter(
        method="filter_by_name",
        help_text="Search by first name or last name (partial match)"
    )
    first_name = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by first name (partial match)"
    )
    last_name = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by last name (partial match)"
    )
    username = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by username (partial match)"
    )
    email = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by email (partial match)"
    )
    
    # Status filters
    is_active = filters.BooleanFilter(
        help_text="Filter by active status (true/false)"
    )
    
    class Meta:
        model = User
        fields = [
            'role',
            'employee_id',
            'student_id',
            'name',
            'first_name',
            'last_name',
            'username',
            'email',
            'is_active',
        ]
    
    def filter_by_name(self, queryset, name, value):
        """
        Filter by first_name OR last_name (combined search).
        """
        from django.db.models import Q
        return queryset.filter(
            Q(first_name__icontains=value) | Q(last_name__icontains=value)
        )


class StudentProfileFilterSet(filters.FilterSet):
    """
    FilterSet for StudentProfile model.
    """
    grade_level = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by grade level"
    )
    roll_number = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by roll number"
    )
    
    # User related filters
    student_name = filters.CharFilter(
        method="filter_by_student_name",
        help_text="Search by student's first or last name"
    )
    
    class Meta:
        model = StudentProfile
        fields = ['grade_level', 'roll_number', 'student_name']
    
    def filter_by_student_name(self, queryset, name, value):
        """Filter by student's user first_name or last_name."""
        from django.db.models import Q
        return queryset.filter(
            Q(user__first_name__icontains=value) | Q(user__last_name__icontains=value)
        )


class TeacherProfileFilterSet(filters.FilterSet):
    """
    FilterSet for TeacherProfile model.
    """
    department = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by department"
    )
    subject_specialization = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by subject specialization"
    )
    employee_code = filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by employee code"
    )
    
    # User related filters
    teacher_name = filters.CharFilter(
        method="filter_by_teacher_name",
        help_text="Search by teacher's first or last name"
    )
    
    class Meta:
        model = TeacherProfile
        fields = ['department', 'subject_specialization', 'employee_code', 'teacher_name']
    
    def filter_by_teacher_name(self, queryset, name, value):
        """Filter by teacher's user first_name or last_name."""
        from django.db.models import Q
        return queryset.filter(
            Q(user__first_name__icontains=value) | Q(user__last_name__icontains=value)
        )
