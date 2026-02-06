from apps.common.models import (
    BaseTimeStampModelMixin,
    BaseAuditModelMixin,
    SoftDeleteModelMixin,
)
from django.db import models


class Course(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    COURSE_TYPE = (
        ("IELTS", "IELTS"),
        ("PTE", "PTE"),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "course"
        unique_together = ("title", "course_type")
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class Section(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    SECTION_CHOICES = (
        ("listening", "Listening"),
        ("reading", "Reading"),
        ("writing", "Writing"),
        ("speaking", "Speaking"),
    )

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="sections"
    )
    name = models.CharField(max_length=20, choices=SECTION_CHOICES)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "sections"
        unique_together = ("course", "name")
        ordering = ("id",)

    def __str__(self):
        return f"{self.course.title} - {self.name}"


class Lesson(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=200)

    file = models.FileField(upload_to="lessons/files/", blank=True, null=True)
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube, Vimeo, or other video URL")
    is_active = models.BooleanField(default=True)
    content = models.TextField()

    order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "lessons"
        unique_together = ("section", "order")
        ordering = ("order",)

    def __str__(self):
        return self.title
