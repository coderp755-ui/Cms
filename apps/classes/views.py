from apps.common.views import AbstractViewSet 
from apps.classes.Serializers.CourseSerializers import CourseSerializer
from apps.classes.Serializers.SectionSerializer import SectionSerializer
from apps.classes.Serializers.LessonSerializers import LessonSerializer
from apps.classes.models import Course, Section, Lesson
from rest_framework.permissions import IsAuthenticated


class CourseViwset(AbstractViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]


class SectionViwset(AbstractViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated]


class LessonViwset(AbstractViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]