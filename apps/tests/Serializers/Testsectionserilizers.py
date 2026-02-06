from rest_framework import serializers
from apps.tests.models import TestSection
from apps.common.serializers import DynamicFieldsModelSerializer


class TestSectionSerializer(DynamicFieldsModelSerializer):
    test_title = serializers.CharField(source="test.title", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)

    class Meta:
        model = TestSection
        fields = [
            "id",
            "test",
            "test_title",
            "section",
            "section_name",
            "duration_minutes",
            "total_marks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def validate_unique_together(self, data):
        test = data.get("test", self.instance.test if self.instance else None)
        section = data.get("section", self.instance.section if self.instance else None)

        qs = TestSection.objects.filter(test=test, section=section)

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "This test-section combination already exists."
            )
        return data
