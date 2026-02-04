from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.classes.views import (
    CourseViewSet,
    SectionViewSet,
    LessonViewSet,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r"course", CourseViewSet, basename="course")
router.register(r"lesson", LessonViewSet, basename="lesson")
router.register(r"sections", SectionViewSet, basename="sections")

urlpatterns = [
    path("", include(router.urls)),
]
