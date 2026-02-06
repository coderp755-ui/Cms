from rest_framework import serializers
from apps.tests.model import Question
from apps.common.serializers import DynamicFieldsModelSerializer

class QuestionSerilizers(DynamicFieldsModelSerializer):
    class Meta:
        model= Question
        feilds=[
            "question_text"
            "question_audio"
            "question_type"
            "marks"
            "order"
            "correct_answer"   

        ]
        read_only_fileds=["created_at", "updated_at","created_by","updated_by"]

        def validate_title(self,value):
            qs=Title.objects.filter(title__iexact=value, is_deleted=False)

            if self.instance:
                qs=qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError("This title already exists.")
            return value    

