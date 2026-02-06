from rest_framework import serializers
from apps.tests.model import TestSection
from apps.common.serializers import DynamicFieldsModelSerializer

class TestSectionSerilizers(DynamicFieldsModelSerializer):
    class Meta:
        model= TestSection
        feilds =[
            "test"
            "section"
            "duration_minutes"
            "total_marks"
        ]
        read_only_fileds=["created_at", "updated_at","created_by","updated_by"]
        
        def validate_titlesection(self,value):
            qs=TestSection.objects.filter(title__iexcat=value, is_deleted = False)

            if self.instance:
                qs=qs.exclude(id=self.instance.id)

            if qs.exits():
                raise serializers.ValidationError("This title already exists.")
            return value        