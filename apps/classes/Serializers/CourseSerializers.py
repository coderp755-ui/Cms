from rest_framework import serializers
from apps.classes.models import Course
from apps.common.serializers import DynamicFieldsModelSerializer


class CourseSerializer(DynamicFieldsModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "description",
            "title",
            "course_type",
            "branch",
            "branch_name",
            "is_active",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "branch_name",
        ]

    def validate_title(self, value):
        qs = Course.objects.filter(title__iexact=value, is_deleted=False)

        # update case ma aafnai record ignore garna
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("This course title already exists.")

        return value

    def validate(self, attrs):
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            # Admin can only create courses for their own branch
            if request.user.role == "admin":
                if not request.user.branch:
                    raise serializers.ValidationError(
                        "Your account is not assigned to any branch. Please contact superadmin."
                    )

                course_branch = attrs.get("branch")
                if course_branch and course_branch != request.user.branch:
                    raise serializers.ValidationError(
                        f"You can only create courses for your branch: {request.user.branch.name}"
                    )

                # Auto-assign admin's branch if not provided
                attrs["branch"] = request.user.branch

            # Superadmin and teacher must specify branch
            if request.user.role in ["superadmin", "teacher"]:
                if not attrs.get("branch"):
                    raise serializers.ValidationError(
                        "Branch is required when creating courses"
                    )

        return attrs
