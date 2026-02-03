from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.classes.views import (
    CourseViwset,
    SectionViwset,
    LessonViwset,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'course', CourseViwset, basename='course')
router.register(r'lesson', LessonViwset, basename='lesson')
router.register(r'sections', SectionViwset, basename='sections')

urlpatterns = [
    path('', include(router.urls)),
]
