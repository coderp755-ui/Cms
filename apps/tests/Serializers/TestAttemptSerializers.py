from rest_framework import serializers
from apps.tests.models import TestAttempt, StudentAnswer
from apps.common.serializers import DynamicFieldsModelSerializer


class StudentAnswerSerializer(DynamicFieldsModelSerializer):
    question_text = serializers.CharField(source="question.question_text", read_only=True)
    selected_option_text = serializers.CharField(
        source="selected_option.option_text", read_only=True
    )

    class Meta:
        model = StudentAnswer
        fields = [
            "id",
            "attempt",
            "question",
            "question_text",
            "selected_option",
            "selected_option_text",
            "answer_text",
            "answer_audio",
            "marks_obtained",
            "is_correct",
            "created_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def validate_unique_together(self, data):
        attempt = data.get("attempt", self.instance.attempt if self.instance else None)
        question = data.get("question", self.instance.question if self.instance else None)

        qs = StudentAnswer.objects.filter(
            attempt=attempt, question=question
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "An answer for this question already exists in this attempt."
            )
        return data


class TestAttemptSerializer(DynamicFieldsModelSerializer):
    student_username = serializers.CharField(source="student.username", read_only=True)
    test_title = serializers.CharField(source="test.title", read_only=True)
    answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = TestAttempt
        fields = [
            "id",
            "student",
            "student_username",
            "test",
            "test_title",
            "started_at",
            "completed_at",
            "is_completed",
            "answers",
            "created_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "started_at",
        ]

    def validate_unique_together(self, data):
        student = data.get("student", self.instance.student if self.instance else None)
        test = data.get("test", self.instance.test if self.instance else None)

        qs = TestAttempt.objects.filter(
            student=student, test=test
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "This student has already attempted this test."
            )
        return data
