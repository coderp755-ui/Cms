from apps.common.models import BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin
from django.db import models

class Course(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    COURSE_TYPE = (
        ('IELTS', 'IELTS'),
        ('PTE', 'PTE'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Section(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    SECTION_CHOICES = (
        ('listening', 'Listening'),
        ('reading', 'Reading'),
        ('writing', 'Writing'),
        ('speaking', 'Speaking'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=20, choices=SECTION_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.title} - {self.name}"

class Lesson(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)

    file = models.FileField(
        upload_to='lessons/files/',
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    content = models.TextField()

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title
