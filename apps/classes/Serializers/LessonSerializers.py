from rest_framework import serializers
from apps.classes.models import Lesson
from apps.common.serializers import DynamicFieldsModelSerializer
import os


class LessonSerializer(DynamicFieldsModelSerializer):
    file_type = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "section",
            "title",
            "file",
            "file_url",
            "file_type",
            "is_active",
            "content",
            "order",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "file_url",
            "file_type",
        ]

    def get_file_type(self, obj):
        """Get file extension/type from uploaded file."""
        if obj.file:
            file_name = obj.file.name
            extension = os.path.splitext(file_name)[1].lower()
            # Remove the dot from extension
            return extension[1:] if extension else None
        return None

    def get_file_url(self, obj):
        """Get full URL of the file."""
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def validate_title(self, value):
        """Validate that lesson title is unique."""
        qs = Lesson.objects.filter(title__iexact=value, is_deleted=False)

        # update case ma aafnai record ignore garna
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("This Lesson title already exists.")

        return value

    def validate_file(self, value):
        """Validate file size only (all file types allowed)."""
        if value:
            # Optional: Check file size (e.g., max 500MB)
            max_size = 500 * 1024 * 1024  # 500MB in bytes
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"File size must not exceed 500MB. Current size: {value.size / (1024 * 1024):.2f}MB"
                )

        return value
