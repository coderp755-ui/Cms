from rest_framework import serializers
from apps.tests.models import BandScoreMapping
from apps.common.serializers import DynamicFieldsModelSerializer


class BandScoreMappingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = BandScoreMapping
        fields = [
            "id",
            "test_type",
            "section",
            "min_score",
            "max_score",
            "band_score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def validate_unique_together(self, data):
        test_type = data.get(
            "test_type", self.instance.test_type if self.instance else None
        )
        section = data.get("section", self.instance.section if self.instance else None)
        min_score = data.get(
            "min_score", self.instance.min_score if self.instance else None
        )
        max_score = data.get(
            "max_score", self.instance.max_score if self.instance else None
        )

        qs = BandScoreMapping.objects.filter(
            test_type=test_type,
            section=section,
            min_score=min_score,
            max_score=max_score,
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("This band score mapping already exists.")
        return data

    def validate(self, data):
        if data.get("min_score") and data.get("max_score"):
            if data["min_score"] >= data["max_score"]:
                raise serializers.ValidationError(
                    "min_score must be less than max_score"
                )
        return data
