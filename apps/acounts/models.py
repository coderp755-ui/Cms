from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.common.models import (
    BaseTimeStampModelMixin,
    BaseAuditModelMixin,
    SoftDeleteModelMixin,
)


class Branch(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    """Branch model for multi-branch management"""

    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "branches"
        ordering = ["name"]
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.name} ({self.code})"


class User(
    AbstractUser, BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin
):
    ROLE_CHOICES = [
        ("superadmin", "Superadmin"),
        ("admin", "Admin"),
        ("teacher", "Teacher"),
        ("student", "Student"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        help_text="Branch assignment for admin, teacher, and student",
    )
    enrolled_courses = models.ManyToManyField(
        "classes.Course",
        blank=True,
        related_name="enrolled_students",
        help_text="Courses the student is enrolled in",
    )

    is_super = models.BooleanField(default=False)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    student_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    # Password management fields
    must_change_password = models.BooleanField(
        default=True, help_text="User must change password on first login"
    )
    password_reset_otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "users"
        unique_together = ("employee_id", "student_id")
        ordering = ["-created_at"]
        verbose_name = "User"

    def save(self, *args, **kwargs):
        # Auto-generate IDs based on role
        if not self.pk:  # Only for new users
            if self.role in ["superadmin", "admin", "teacher"] and not self.employee_id:
                self.employee_id = self.generate_employee_id()
            elif self.role == "student" and not self.student_id:
                self.student_id = self.generate_student_id()
        super().save(*args, **kwargs)

    def generate_employee_id(self):
        """Generate unique employee ID"""
        import random

        while True:
            emp_id = f"EMP{random.randint(10000, 99999)}"
            if not User.objects.filter(employee_id=emp_id).exists():
                return emp_id

    def generate_student_id(self):
        """Generate unique student ID"""
        import random

        while True:
            std_id = f"STD{random.randint(10000, 99999)}"
            if not User.objects.filter(student_id=std_id).exists():
                return std_id

    def generate_otp(self):
        """Generate 6-digit OTP and set expiry time"""
        import random
        from django.utils import timezone
        from datetime import timedelta

        self.password_reset_otp = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.otp_expires_at = timezone.now() + timedelta(
            minutes=10
        )  # OTP valid for 10 minutes
        self.save()
        return self.password_reset_otp

    def verify_otp(self, otp):
        """Verify if OTP is valid and not expired"""
        from django.utils import timezone

        if not self.password_reset_otp or not self.otp_expires_at:
            return False

        if self.password_reset_otp != otp:
            return False

        if timezone.now() > self.otp_expires_at:
            return False

        return True

    def clear_otp(self):
        """Clear OTP after successful password reset"""
        self.password_reset_otp = None
        self.otp_created_at = None
        self.otp_expires_at = None
        self.save()

    def __str__(self):
        if self.role == "student" and self.student_id:
            return f"{self.username} ({self.get_role_display()}) - {self.student_id}"
        elif self.role in ["superadmin", "admin", "teacher"] and self.employee_id:
            return f"{self.username} ({self.get_role_display()}) - {self.employee_id}"
        return f"{self.username} ({self.get_role_display()})"

    def is_superuser_role(self):
        return self.role == "superuser"

    def is_admin_role(self):
        return self.role == "admin"

    def is_teacher_role(self):
        return self.role == "teacher"

    def is_student_role(self):
        return self.role == "student"


class UserProfile(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Basic Info
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", null=True, blank=True
    )

    # Contact Info
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(max_length=300, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)

    # Additional Info
    join_date = models.DateField(auto_now_add=True)
    nationality = models.CharField(max_length=50, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)

    # Social Links (optional)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Status
    is_active_profile = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        db_table = "user_profiles"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class StudentProfile(
    BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin
):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, limit_choices_to={"role": "student"}
    )

    # Academic Info
    grade_level = models.CharField(max_length=20, blank=True)
    roll_number = models.CharField(max_length=20, blank=True)
    admission_date = models.DateField(null=True, blank=True)

    # Parent/Guardian Info
    father_name = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=100, blank=True)
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    guardian_email = models.EmailField(blank=True)

    # Additional Student Info
    previous_school = models.CharField(max_length=200, blank=True)
    medical_conditions = models.TextField(blank=True)
    extracurricular_activities = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - Grade {self.grade_level}"

    class Meta:
        db_table = "student_profiles"
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"


class TeacherProfile(
    BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin
):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, limit_choices_to={"role": "teacher"}
    )

    # Professional Info
    employee_code = models.CharField(max_length=20, unique=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    subject_specialization = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)

    # Employment Details
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ("full_time", "Full Time"),
            ("part_time", "Part Time"),
            ("contract", "Contract"),
        ],
        default="full_time",
    )

    # Teaching Details
    classes_assigned = models.TextField(
        help_text="Comma separated class names", blank=True
    )
    subjects_teaching = models.TextField(
        help_text="Comma separated subjects", blank=True
    )

    # Professional Development
    certifications = models.TextField(blank=True)
    training_completed = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.department}"

    class Meta:
        db_table = "teacher_profiles"
        verbose_name = "Teacher Profile"
        verbose_name_plural = "Teacher Profiles"
