from rest_framework import serializers
from apps.classes.models import Section
from apps.common.serializers import DynamicFieldsModelSerializer


class SectionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Section
        fields = [
            "id",
            "course",
            "name",
            "is_active",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    
    def validate(self, attrs):
        """Validate that course + name combination is unique."""
        course = attrs.get('course')
        name = attrs.get('name')
        
        # Check if this is an update or create
        instance = self.instance
        
        if course and name:
            # Check if section already exists
            existing = Section.objects.filter(course=course, name=name)
            
            # If updating, exclude current instance
            if instance:
                existing = existing.exclude(id=instance.id)
            
            if existing.exists():
                raise serializers.ValidationError({
                    'name': f'A section with name "{name}" already exists for this course.'
                })
        
        return attrs
