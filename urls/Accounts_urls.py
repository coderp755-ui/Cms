from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.acounts.views import (
    UserViewSet,
    UserProfileViewSet,
    StudentProfileViewSet,
    TeacherProfileViewSet,
    LogoutView,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"profiles", UserProfileViewSet, basename="profiles")
router.register(r"students", StudentProfileViewSet, basename="students")
router.register(r"teachers", TeacherProfileViewSet, basename="teachers")

urlpatterns = [
    path("", include(router.urls)),
    path("logout/", LogoutView.as_view(), name="logout"),
]
