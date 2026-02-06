from rest_framework import serializers
from apps.tests.model import Test
from apps.common.serializers import DynamicFieldsModelSerializer

class TestSerilizers(DynamicFieldsModelSerializer):
    class Meta:
        model = Test
        feilds =[
            "id",
            "course"
            "description"
            "test_kind"
            "duration_minutes"
            "total_minutes"
            "is_active"
        ]
        read_only_fileds=["created_at", "updated_at","created_by","updated_by"]

        def validate_title(self,value):
            qs=Title.objects.filter(title__iexact=value, is_deleted=False)

            if self.instance:
                qs=qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError("This title already exists.")
            return value        