from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.common.serializers import DynamicFieldsModelSerializer
from apps.acounts.models import User, UserProfile, StudentProfile, TeacherProfile


class UserSerializer(DynamicFieldsModelSerializer):
    """
    User serializer with dynamic field selection and role-based ID display.
    """

    password = serializers.CharField(
        write_only=True, validators=[validate_password], required=False
    )
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
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
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        if "password" in attrs and "password_confirm" in attrs:
            if attrs["password"] != attrs["password_confirm"]:
                raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserProfileSerializer(DynamicFieldsModelSerializer):
    """
    User profile serializer with audit fields and dynamic field selection.
    """

    user_id = serializers.IntegerField(write_only=True)

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
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]


class StudentProfileSerializer(DynamicFieldsModelSerializer):
    """
    Student profile serializer with academic and parent information.
    """

    user_id = serializers.IntegerField(write_only=True)

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
            "current_gpa",
            "attendance_percentage",
            "previous_school",
            "medical_conditions",
            "extracurricular_activities",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            if user.role != "student":
                raise serializers.ValidationError("User must have 'student' role")
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value


class TeacherProfileSerializer(DynamicFieldsModelSerializer):
    """
    Teacher profile serializer with professional and employment information.
    """

    user_id = serializers.IntegerField(write_only=True)

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
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            if user.role != "teacher":
                raise serializers.ValidationError("User must have 'teacher' role")
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value


class Self(serializers.Serializer):
    def to_representation(self, instance):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            return {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_active": user.is_active,
                "student_id": user.student_id if user.role == "student" else None,
                "employee_id": user.employee_id
                if user.role in ["superadmin", "admin", "teacher"]
                else None,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
            }
        return {}
