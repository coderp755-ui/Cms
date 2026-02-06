from rest_framework import serializers
from apps.tests.model import QuestionOption
from apps.common.serializers import DynamicFieldsModelSerializer

class QuestionOptionSerilizers(DynamicFieldsModelSerializer):
    class Meta:
        model = QuestionOption
        fields=[
            "question"
            "option_text"
            "is_correct"

        ]
        read_only_fileds=["created_at", "updated_at","created_by","updated_by"]

        def validate_title(self,value):
            qs=QuestionOption.objects.filter(title__iexact=value, is_deleted=False)
            
            if self.instance:
                qs=qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError("This title already exists.")
            return value        