from rest_framework import serializers
from .models import BandScoreMapping
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
            # "created_at",
            # "updated_at",
            # "created_by",
            # "updated_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at","created_by","updated_by",]

    def validate(self, attrs):
        """
        Prevent overlapping score ranges for same test_type & section
        """
        test_type = attrs.get("test_type")
        section = attrs.get("section")
        min_score = attrs.get("min_score")
        max_score = attrs.get("max_score")

        if min_score >= max_score:
            raise serializers.ValidationError(
                {"min_score": "min_score must be less than max_score"}
            )

        qs = BandScoreMapping.objects.filter(
            test_type=test_type,
            section=section,
        )

        # Update case handle
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        # Overlapping range check
        if qs.filter(
            min_score__lt=max_score,
            max_score__gt=min_score,
        ).exists():
            raise serializers.ValidationError(
                "Score range overlaps with existing band mapping"
            )

        return attrs
