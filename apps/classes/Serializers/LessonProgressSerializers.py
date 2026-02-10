from rest_framework import serializers
from apps.classes.models import LessonProgress


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "user",
            "user_username",
            "lesson",
            "lesson_title",
            "is_completed",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "completed_at",
        ]

    def create(self, validated_data):
        """Create or update lesson progress."""
        user = validated_data.get("user")
        lesson = validated_data.get("lesson")
        
        progress, created = LessonProgress.objects.get_or_create(
            user=user,
            lesson=lesson,
            defaults=validated_data
        )
        
        if not created:
            for key, value in validated_data.items():
                setattr(progress, key, value)
            progress.save()
        
        return progress
