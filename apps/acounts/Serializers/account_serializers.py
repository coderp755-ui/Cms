from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.common.serializers import DynamicFieldsModelSerializer
from apps.acounts.models import Branch, User, UserProfile, StudentProfile, TeacherProfile


class BranchSerializer(DynamicFieldsModelSerializer):
    """
    Branch serializer for multi-branch management.
    """
    
    class Meta:
        model = Branch
        fields = [
            "id",
            "name",
            "code",
            "address",
            "phone",
            "email",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]


class UserSerializer(DynamicFieldsModelSerializer):
    """
    User serializer with dynamic field selection and role-based ID display.
    """

    password = serializers.CharField(
        write_only=True, validators=[validate_password], required=False
    )
    password_confirm = serializers.CharField(write_only=True, required=False)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    enrolled_courses_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "branch",
            "branch_name",
            "enrolled_courses",
            "enrolled_courses_details",
            "is_super",
            "employee_id",
            "student_id",
            "is_active",
            "date_joined",
            "is_deleted",
            "last_login",
            "password",
            "password_confirm",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
            "employee_id",
            "student_id",
            "branch_name",
            "enrolled_courses_details",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }
    
    def get_enrolled_courses_details(self, obj):
        """Return enrolled courses with basic details"""
        if obj.role == "student" and obj.enrolled_courses.exists():
            return [
                {
                    "id": course.id,
                    "title": course.title,
                    "course_type": course.course_type,
                    "branch": course.branch.name if course.branch else None,
                }
                for course in obj.enrolled_courses.filter(is_active=True, is_deleted=False)
            ]
        return []

    def validate(self, attrs):
        request = self.context.get('request')
        
        # Password validation
        if "password" in attrs and "password_confirm" in attrs:
            if attrs["password"] != attrs["password_confirm"]:
                raise serializers.ValidationError("Passwords don't match")
        
        # Branch-based user creation validation
        if request and request.user.is_authenticated:
            user_role = attrs.get('role')
            user_branch = attrs.get('branch')
            
            # Only superadmin can create admins
            if user_role == 'admin' and request.user.role != 'superadmin':
                raise serializers.ValidationError(
                    "Only superadmin can create admin users"
                )
            
            # Admin can only create users for their own branch
            if request.user.role == 'admin':
                if not request.user.branch:
                    raise serializers.ValidationError(
                        "Your account is not assigned to any branch. Please contact superadmin."
                    )
                
                # Force the branch to be the admin's branch
                if user_role in ['admin', 'teacher', 'student']:
                    if user_branch and user_branch != request.user.branch:
                        raise serializers.ValidationError(
                            f"You can only create users for your branch: {request.user.branch.name}"
                        )
                    # Auto-assign admin's branch if not provided
                    attrs['branch'] = request.user.branch
            
            # Superadmin must assign branch when creating admin/teacher/student
            if request.user.role == 'superadmin' and user_role in ['admin', 'teacher', 'student']:
                if not user_branch:
                    raise serializers.ValidationError(
                        f"Branch is required when creating {user_role} users"
                    )
        
        # Validate enrolled courses belong to the same branch as user
        if "enrolled_courses" in attrs:
            branch = attrs.get("branch")
            enrolled_courses = attrs.get("enrolled_courses", [])
            
            if branch and enrolled_courses:
                for course in enrolled_courses:
                    if course.branch and course.branch != branch:
                        raise serializers.ValidationError(
                            f"Course '{course.title}' belongs to branch '{course.branch.name}'. "
                            f"All enrolled courses must be from the user's branch: '{branch.name}'"
                        )
        
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        
        # Handle enrolled_courses separately (ManyToMany field)
        enrolled_courses = validated_data.pop("enrolled_courses", [])
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Set enrolled courses after creating the user
        if enrolled_courses:
            user.enrolled_courses.set(enrolled_courses)
        
        return user

    def update(self, instance, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password", None)
        
        # Handle enrolled_courses separately (ManyToMany field)
        enrolled_courses = validated_data.pop("enrolled_courses", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        
        # Set enrolled courses after saving the instance
        if enrolled_courses is not None:
            instance.enrolled_courses.set(enrolled_courses)
        
        return instance


class UserProfileSerializer(DynamicFieldsModelSerializer):
    """
    User profile serializer with audit fields and dynamic field selection.
    """

    user_id = serializers.IntegerField(write_only=True, required=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "user_id",
            "bio",
            "birth_date",
            "profile_picture",
            "phone_number",
            "address",
            "emergency_contact",
            "join_date",
            "nationality",
            "blood_group",
            "facebook_url",
            "linkedin_url",
            "is_active_profile",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by", "user"]
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        validated_data['user'] = user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Remove user_id if present (can't change user)
        validated_data.pop('user_id', None)
        return super().update(instance, validated_data)


class StudentProfileSerializer(DynamicFieldsModelSerializer):
    """
    Student profile serializer with academic and parent information.
    """

    user_id = serializers.IntegerField(write_only=True, required=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user",
            "user_id",
            "grade_level",
            "roll_number",
            "admission_date",
            "father_name",
            "mother_name",
            "guardian_name",
            "guardian_phone",
            "guardian_email",
            "previous_school",
            "medical_conditions",
            "extracurricular_activities",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by", "user"]

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            if user.role != "student":
                raise serializers.ValidationError("User must have 'student' role")
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        validated_data['user'] = user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Remove user_id if present (can't change user)
        validated_data.pop('user_id', None)
        return super().update(instance, validated_data)


class TeacherProfileSerializer(DynamicFieldsModelSerializer):
    """
    Teacher profile serializer with professional and employment information.
    """

    user_id = serializers.IntegerField(write_only=True, required=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            "id",
            "user",
            "user_id",
            "employee_code",
            "department",
            "subject_specialization",
            "qualification",
            "experience_years",
            "hire_date",
            "salary",
            "employment_type",
            "classes_assigned",
            "subjects_teaching",
            "certifications",
            "training_completed",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by", "user"]

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            if user.role != "teacher":
                raise serializers.ValidationError("User must have 'teacher' role")
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        validated_data['user'] = user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Remove user_id if present (can't change user)
        validated_data.pop('user_id', None)
        return super().update(instance, validated_data)


class Self(serializers.Serializer):
    def to_representation(self, instance):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            
            # Get enrolled courses for students
            enrolled_courses = []
            if user.role == "student" and user.enrolled_courses.exists():
                enrolled_courses = [
                    {
                        "id": course.id,
                        "title": course.title,
                        "course_type": course.course_type,
                    }
                    for course in user.enrolled_courses.filter(is_active=True, is_deleted=False)
                ]
            
            return {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "branch": user.branch.name if user.branch else None,
                "branch_id": user.branch.id if user.branch else None,
                "enrolled_courses": enrolled_courses,
                "is_active": user.is_active,
                "student_id": user.student_id if user.role == "student" else None,
                "employee_id": user.employee_id
                if user.role in ["superadmin", "admin", "teacher"]
                else None,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
            }
        return {}
