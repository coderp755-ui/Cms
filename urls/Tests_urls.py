from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.tests.views import (
    TestViewSet,
    TestSectionViewSet,
    QuestionViewSet,
    QuestionOptionViewSet,
    TestAttemptViewSet,
    StudentAnswerViewSet,
    TestResultViewSet,
    SectionResultViewSet,
    ManualEvaluationViewSet,
    BandScoreMappingViewSet,
)

router = DefaultRouter()
router.register(r"tests", TestViewSet, basename="test")
router.register(r"test-sections", TestSectionViewSet, basename="test-section")
router.register(r"questions", QuestionViewSet, basename="question")
router.register(r"question-options", QuestionOptionViewSet, basename="question-option")
router.register(r"test-attempts", TestAttemptViewSet, basename="test-attempt")
router.register(r"student-answers", StudentAnswerViewSet, basename="student-answer")
router.register(r"test-results", TestResultViewSet, basename="test-result")
router.register(r"section-results", SectionResultViewSet, basename="section-result")
router.register(
    r"manual-evaluations", ManualEvaluationViewSet, basename="manual-evaluation"
)
router.register(
    r"band-score-mappings", BandScoreMappingViewSet, basename="band-score-mapping"
)

urlpatterns = [
    path("", include(router.urls)),
]
