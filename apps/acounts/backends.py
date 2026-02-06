"""
Custom authentication backend to prevent deleted users from logging in.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class CustomAuthBackend(ModelBackend):
    """
    Custom authentication backend that prevents soft-deleted users from logging in.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user and check if they are not soft-deleted.
        """
        try:
            # Get user by username or email
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

        # Check if user is soft-deleted
        if hasattr(user, "is_deleted") and user.is_deleted:
            return None

        # Check if user is active
        if not user.is_active:
            return None

        # Check password
        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        """
        Get user by ID, but only if they are not soft-deleted.
        """
        try:
            user = User.objects.get(pk=user_id)
            # Check if user is soft-deleted
            if hasattr(user, "is_deleted") and user.is_deleted:
                return None
            return user
        except User.DoesNotExist:
            return None


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that prevents deleted users from getting tokens.
    """

    def validate(self, attrs):
        """
        Validate credentials and check if user is not deleted.
        """
        # Get username from attrs
        username = attrs.get("username")

        try:
            # Check if user exists and is not deleted
            user = User.objects.get(username=username)

            if hasattr(user, "is_deleted") and user.is_deleted:
                raise AuthenticationFailed(
                    "This account has been deleted. Please contact administrator."
                )

            if not user.is_active:
                raise AuthenticationFailed(
                    "This account is inactive. Please contact administrator."
                )

        except User.DoesNotExist:
            pass  # Let parent class handle invalid credentials

        # Call parent validation
        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view using our custom serializer.
    """

    serializer_class = CustomTokenObtainPairSerializer
