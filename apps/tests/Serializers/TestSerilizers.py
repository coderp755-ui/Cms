from rest_framework import serializers
from apps.tests.models import Test
from apps.common.serializers import DynamicFieldsModelSerializer


class TestSerializer(DynamicFieldsModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Test
        fields = [
            "id",
            "course",
            "course_title",
            "title",
            "description",
            "test_kind",
            "duration_minutes",
            "total_marks",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def validate_title(self, value):
        qs = Test.objects.filter(title__iexact=value)

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("This title already exists.")
        return value
