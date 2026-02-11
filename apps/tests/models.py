from django.db import models
from apps.common.models import (
    BaseTimeStampModelMixin,
    BaseAuditModelMixin,
    SoftDeleteModelMixin,
)
from apps.classes.models import Course, Section
from apps.acounts.models import User


class Test(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    TEST_KIND = (
        ("mock", "Mock Test"),
        ("practice", "Practice Test"),
        ("sectional", "Sectional Test"),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="tests")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    test_kind = models.CharField(max_length=20, choices=TEST_KIND)
    duration_minutes = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "Test"
        unique_together = ("course", "title")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class TestSection(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="sections")
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    duration_minutes = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()

    class Meta:
        db_table = "Test_Sections"
        unique_together = ("test", "section")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.test.title} - {self.section.name}"


class Question(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    QUESTION_TYPE = (
        ("mcq", "Multiple Choice"),
        ("text", "Text Answer"),
        ("essay", "Essay"),
        ("audio", "Audio Based"),
    )

    test_section = models.ForeignKey(
        TestSection, on_delete=models.CASCADE, related_name="questions"
    )
    question_text = models.TextField(blank=True)
    question_audio = models.FileField(
        upload_to="tests/questions/audio/", blank=True, null=True
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE)
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)
    correct_answer = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "Test_Questions"
        unique_together = ("test_section", "order")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["test_section", "order"])]

    def __str__(self):
        return f"Q{self.id} ({self.question_type})"


class QuestionOption(
    BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin
):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "Test_QuestionsOptions"
        ordering = ("-created_at",)
        unique_together = ("question", "option_text")
        indexes = [models.Index(fields=["question"])]

    def __str__(self):
        return self.option_text


class TestAttempt(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
        related_name="test_attempts",
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="attempts")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "TestAttempt"
        ordering = ("-created_at",)
        unique_together = ("student", "test")
        indexes = [models.Index(fields=["student", "test"])]

    def __str__(self):
        return f"{self.student.username} - {self.test.title}"


class StudentAnswer(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    attempt = models.ForeignKey(
        TestAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(
        QuestionOption, on_delete=models.SET_NULL, blank=True, null=True
    )
    answer_text = models.TextField(blank=True, null=True)
    answer_audio = models.FileField(
        upload_to="tests/answers/audio/", blank=True, null=True
    )
    marks_obtained = models.FloatField(default=0)
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "Test_StudentAnswer"
        ordering = ("-created_at",)
        unique_together = ("attempt", "question")
        indexes = [models.Index(fields=["attempt", "question"])]

    def __str__(self):
        return f"{self.attempt.student.username} - Q{self.question.id}"


class TestResult(BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    attempt = models.OneToOneField(
        TestAttempt, on_delete=models.CASCADE, related_name="result"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"role": "student"}
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    total_marks = models.FloatField()
    obtained_marks = models.FloatField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    band_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    is_passed = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "Test_Results"
        unique_together = ("attempt", "student", "test")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.student.username} - {self.test.title}"


class SectionResult(BaseTimeStampModelMixin, SoftDeleteModelMixin):
    result = models.ForeignKey(
        TestResult, on_delete=models.CASCADE, related_name="section_results"
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    total_marks = models.FloatField()
    obtained_marks = models.FloatField(default=0)
    band_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    is_checked = models.BooleanField(default=False)

    class Meta:
        db_table = "Test_SectionsResult"
        ordering = ("-created_at",)
        unique_together = ("result", "section")

    def __str__(self):
        return f"{self.section.name} - {self.result.student.username}"


class ManualEvaluation(BaseTimeStampModelMixin, BaseAuditModelMixin):
    answer = models.OneToOneField(
        StudentAnswer, on_delete=models.CASCADE, related_name="manual_evaluation"
    )
    checked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, limit_choices_to={"role": "teacher"}
    )
    criteria_score = models.JSONField(help_text="e.g. fluency, grammar, coherence")
    obtained_marks = models.FloatField()
    feedback = models.TextField(blank=True)
    is_final = models.BooleanField(default=False)

    class Meta:
        db_table = "Test_ManualEvaluations"
        ordering = ("-created_at",)
        unique_together = ("answer", "checked_by")

    def __str__(self):
        return f"Evaluation - Q{self.answer.question.id}"


class BandScoreMapping(BaseTimeStampModelMixin, BaseAuditModelMixin):
    test_type = models.CharField(
        max_length=10, choices=(("IELTS", "IELTS"), ("PTE", "PTE"))
    )
    section = models.CharField(
        max_length=20,
        choices=(
            ("listening", "Listening"),
            ("reading", "Reading"),
            ("writing", "Writing"),
            ("speaking", "Speaking"),
        ),
    )
    min_score = models.FloatField()
    max_score = models.FloatField()
    band_score = models.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        db_table = "Test_BandMapping"
        ordering = ("-created_at",)
        unique_together = ("test_type", "section", "min_score", "max_score")

    def __str__(self):
        return f"{self.section} → {self.band_score}"
