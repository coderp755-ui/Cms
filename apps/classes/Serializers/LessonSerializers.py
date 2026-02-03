from rest_framework import serializers
from apps.classes.models import Lesson
from apps.common.serializers import DynamicFieldsModelSerializer

class LessonSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id',
            'section',
            'title',
            'is_active',
            'content',
            'order',
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

        def validate_title(self, value):
            qs = Lesson.objects.filter(
                title__iexact=value,
                is_deleted=False
            )

            # update case ma aafnai record ignore garna
            if self.instance:
                qs = qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError(
                    "This Lesson title already exists."
                )

            return value

