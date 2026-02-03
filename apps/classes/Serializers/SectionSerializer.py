from rest_framework import serializers
from apps.classes.models import Section
from apps.common.serializers import DynamicFieldsModelSerializer

class SectionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Section
        fields = [
            'id',
            'course',
            'name',
            'is_active',
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

