from rest_framework import serializers
from apps.tests.models import TestResult, SectionResult
from apps.common.serializers import DynamicFieldsModelSerializer


class SectionResultSerializer(DynamicFieldsModelSerializer):
    section_name = serializers.CharField(source="section.name", read_only=True)

    class Meta:
        model = SectionResult
        fields = [
            "id",
            "result",
            "section",
            "section_name",
            "total_marks",
            "obtained_marks",
            "band_score",
            "is_checked",
            "created_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_unique_together(self, data):
        result = data.get("result", self.instance.result if self.instance else None)
        section = data.get("section", self.instance.section if self.instance else None)

        qs = SectionResult.objects.filter(
            result=result, section=section
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "A result for this section already exists."
            )
        return data


class TestResultSerializer(DynamicFieldsModelSerializer):
    student_username = serializers.CharField(source="student.username", read_only=True)
    test_title = serializers.CharField(source="test.title", read_only=True)
    section_results = SectionResultSerializer(many=True, read_only=True)

    class Meta:
        model = TestResult
        fields = [
            "id",
            "attempt",
            "student",
            "student_username",
            "test",
            "test_title",
            "total_marks",
            "obtained_marks",
            "percentage",
            "band_score",
            "is_passed",
            "is_published",
            "section_results",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def validate_unique_together(self, data):
        attempt = data.get("attempt", self.instance.attempt if self.instance else None)
        student = data.get("student", self.instance.student if self.instance else None)
        test = data.get("test", self.instance.test if self.instance else None)

        qs = TestResult.objects.filter(
            attempt=attempt, student=student, test=test
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "A result for this attempt already exists."
            )
        return data
