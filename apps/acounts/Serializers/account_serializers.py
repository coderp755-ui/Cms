from rest_framework import serializers
from django.contrib.auth.models import User
form apps.common.serializers import DynamicFieldsModelSerializer

class UsersSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name','is_super', 'employee_id','student_id']
        readonly feilds = ['created_at','']


class 