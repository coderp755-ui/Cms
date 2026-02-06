from rest_framework import serializers
from django.db import models
from apps.classes.models import Lesson
from apps.common.serializers import DynamicFieldsModelSerializer
import os


class LessonSerializer(DynamicFieldsModelSerializer):
    file_type = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    google_drive_preview_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            "id",
            "section",
            "title",
            "file",
            "file_url",
            "file_type",
            "google_drive_preview_url",
            "video_url",
            "is_active",
            "content",
            "order",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
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
    
    def get_google_drive_preview_url(self, obj):
        """Get Google Drive preview URL for documents (PDF, DOC, etc.)."""
        if obj.file:
            file_url = self.get_file_url(obj)
            file_type = self.get_file_type(obj)
            
            # Document types that can be previewed in Google Drive viewer
            previewable_types = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt']
            
            if file_type in previewable_types:
                # Google Drive viewer URL
                return f"https://drive.google.com/viewerng/viewer?embedded=true&url={file_url}"
        return None

    def create(self, validated_data):
        """Auto-assign order if not provided."""
        if 'order' not in validated_data or validated_data['order'] == 1:
            # Get the max order for this section
            section = validated_data.get('section')
            max_order = Lesson.objects.filter(
                section=section, 
                is_deleted=False
            ).aggregate(models.Max('order'))['order__max']
            
            # Assign next order number
            validated_data['order'] = (max_order or 0) + 1
        
        return super().create(validated_data)
    
    def validate(self, attrs):
        """Validate that section + order combination is unique."""
        section = attrs.get('section')
        order = attrs.get('order', 1)
        
        # Check if this section + order combination already exists
        qs = Lesson.objects.filter(section=section, order=order, is_deleted=False)
        
        # Exclude current instance during update
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        
        if qs.exists():
            raise serializers.ValidationError({
                'order': f'A lesson with order {order} already exists in this section. Please use a different order number.'
            })
        
        return attrs
    
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
