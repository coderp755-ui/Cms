from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.acounts.views import (
    BranchViewSet,
    UserViewSet,
    UserProfileViewSet,
    StudentProfileViewSet,
    TeacherProfileViewSet,
    LogoutView,
    SelfView,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r"branches", BranchViewSet, basename="branches")
router.register(r"users", UserViewSet, basename="users")
router.register(r"user-profiles", UserProfileViewSet, basename="user-profiles")
router.register(r"student-profiles", StudentProfileViewSet, basename="student-profiles")
router.register(r"teacher-profiles", TeacherProfileViewSet, basename="teacher-profiles")

urlpatterns = [
    path("", include(router.urls)),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("self/", SelfView.as_view(), name="self"),
]
