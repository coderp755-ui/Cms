from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.classes.views import (
    CourseViewSet,
    SectionViewSet,
    LessonViewSet,
    LessonProgressViewSet,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r"course", CourseViewSet, basename="course")
router.register(r"lesson", LessonViewSet, basename="lesson")
router.register(r"sections", SectionViewSet, basename="sections")
router.register(r"lesson-progress", LessonProgressViewSet, basename="lesson-progress")

urlpatterns = [
    path("", include(router.urls)),
]
