from rest_framework import serializers
from apps.tests.models import Question, QuestionOption
from apps.common.serializers import DynamicFieldsModelSerializer


class QuestionOptionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = QuestionOption
        fields = [
            "id",
            "option_text",
            "is_correct",
            "created_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]


class QuestionSerializer(DynamicFieldsModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    test_section_title = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "test_section",
            "test_section_title",
            "question_text",
            "question_audio",
            "question_type",
            "marks",
            "order",
            "correct_answer",
            "options",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def get_test_section_title(self, obj):
        return f"{obj.test_section.test.title} - {obj.test_section.section.name}"

    def validate_unique_together(self, data):
        test_section = data.get(
            "test_section",
            self.instance.test_section if self.instance else None,
        )
        order = data.get("order", self.instance.order if self.instance else None)

        qs = Question.objects.filter(
            test_section=test_section, order=order
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "A question with this order already exists in this test section."
            )
        return data
