from rest_framework import serializers
from apps.tests.models import ManualEvaluation
from apps.common.serializers import DynamicFieldsModelSerializer


class ManualEvaluationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ManualEvaluation
        fields = [
            "id",
            "answer",
            "checked_by",
            "criteria_score",
            "obtained_marks",
            "feedback",
            "is_final",
        ]
        extra_kwargs = {
            "answer": {"required": True},
            "criteria_score": {"required": True},
            "obtained_marks": {"required": True},
        }
        read_only_fields = (
            "id",
            "checked_by",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        answer = attrs.get("answer")
        criteria_score = attrs.get("criteria_score")
        obtained_marks = attrs.get("obtained_marks")
        is_final = attrs.get("is_final", False)

        if ManualEvaluation.objects.filter(answer=answer).exists():
            raise serializers.ValidationError({
                "answer": "This answer has already been evaluated."
            })

        if not isinstance(criteria_score, dict):
            raise serializers.ValidationError({
                "criteria_score": "Criteria score must be a dictionary."
            })

        total_criteria_marks = 0
        for key, value in criteria_score.items():
            if not isinstance(value, (int, float)):
                raise serializers.ValidationError({
                    "criteria_score": f"Invalid score for '{key}'. Must be number."
                })
            total_criteria_marks += value

        if obtained_marks > total_criteria_marks:
            raise serializers.ValidationError({
                "obtained_marks": "Obtained marks cannot exceed criteria total."
            })

        if is_final and obtained_marks <= 0:
            raise serializers.ValidationError({
                "obtained_marks": "Final evaluation must have obtained marks."
            })

        return attrs
