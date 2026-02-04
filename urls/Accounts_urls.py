from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.acounts.views import (
    UserViewSet,
    UserProfileViewSet,
    StudentProfileViewSet,
    TeacherProfileViewSet,
    LogoutView,
    SelfView,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"usersprofiles", UserProfileViewSet, basename="profiles")
router.register(r"studentsprofile", StudentProfileViewSet, basename="students")
router.register(r"teachersprofile", TeacherProfileViewSet, basename="teachers")

urlpatterns = [
    path("", include(router.urls)),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("self/", SelfView.as_view(), name="self"),
]
