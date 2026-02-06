from rest_framework import serializers
from apps.tests.models import QuestionOption
from apps.common.serializers import DynamicFieldsModelSerializer


class QuestionOptionDetailSerializer(DynamicFieldsModelSerializer):
    question_text = serializers.CharField(source="question.question_text", read_only=True)

    class Meta:
        model = QuestionOption
        fields = [
            "id",
            "question",
            "question_text",
            "option_text",
            "is_correct",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def validate_unique_together(self, data):
        question = data.get("question", self.instance.question if self.instance else None)
        option_text = data.get(
            "option_text", self.instance.option_text if self.instance else None
        )

        qs = QuestionOption.objects.filter(
            question=question, option_text__iexact=option_text
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("This option already exists for this question.")
        return data
