from rest_framework import serializers
from apps.classes.models import Course
from apps.common.serializers import DynamicFieldsModelSerializer


class CourseSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "description",
            "title",
            "course_type",
            "is_active",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

        def validate_title(self, value):
            qs = Course.objects.filter(title__iexact=value, is_deleted=False)

            # update case ma aafnai record ignore garna
            if self.instance:
                qs = qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError("This course title already exists.")

            return value
