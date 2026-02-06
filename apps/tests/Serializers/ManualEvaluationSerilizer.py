from rest_framework import serializers
from apps.tests.models import ManualEvaluation
from apps.common.serializers import DynamicFieldsModelSerializer


class ManualEvaluationSerializer(DynamicFieldsModelSerializer):
    answer_id = serializers.IntegerField(source="answer.id", read_only=True)
    question_text = serializers.CharField(
        source="answer.question.question_text", read_only=True
    )
    student_username = serializers.CharField(
        source="answer.attempt.student.username", read_only=True
    )
    checked_by_username = serializers.CharField(
        source="checked_by.username", read_only=True
    )

    class Meta:
        model = ManualEvaluation
        fields = [
            "id",
            "answer",
            "answer_id",
            "question_text",
            "student_username",
            "checked_by",
            "checked_by_username",
            "criteria_score",
            "obtained_marks",
            "feedback",
            "is_final",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def validate_unique_together(self, data):
        answer = data.get("answer", self.instance.answer if self.instance else None)
        checked_by = data.get("checked_by", self.instance.checked_by if self.instance else None)

        qs = ManualEvaluation.objects.filter(
            answer=answer, checked_by=checked_by
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "This answer has already been evaluated by this teacher."
            )
        return data
