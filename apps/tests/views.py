from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.tests.models import (
    Test,
    TestSection,
    Question,
    QuestionOption,
    TestAttempt,
    StudentAnswer,
    TestResult,
    SectionResult,
    ManualEvaluation,
    BandScoreMapping,
)
from apps.tests.Serializers.TestSerilizers import TestSerializer
from apps.tests.Serializers.Testsectionserilizers import TestSectionSerializer
from apps.tests.Serializers.Questionserilizers import (
    QuestionSerializer,
    QuestionOptionSerializer,
)
from apps.tests.Serializers.QuestionOptionserilizers import (
    QuestionOptionDetailSerializer,
)
from apps.tests.Serializers.TestAttemptSerializers import (
    TestAttemptSerializer,
    StudentAnswerSerializer,
)
from apps.tests.Serializers.TestResultSerializers import (
    TestResultSerializer,
    SectionResultSerializer,
)
from apps.tests.Serializers.ManualEvaluationSerilizer import ManualEvaluationSerializer
from apps.tests.Serializers.BandScoreMappingSerilizers import BandScoreMappingSerializer
from apps.common.paginations.default_paginations import CustomDefaultPagination


class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["course", "test_kind", "is_active"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["get"])
    def sections(self, request, pk=None):
        test = self.get_object()
        sections = test.sections.filter(is_deleted=False)
        serializer = TestSectionSerializer(sections, many=True)
        return Response(serializer.data)


class TestSectionViewSet(viewsets.ModelViewSet):
    queryset = TestSection.objects.all()
    serializer_class = TestSectionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["test", "section"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["get"])
    def questions(self, request, pk=None):
        test_section = self.get_object()
        questions = test_section.questions.filter(is_deleted=False)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["test_section", "question_type"]
    search_fields = ["question_text"]
    ordering_fields = ["order", "created_at"]
    ordering = ["order"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["get"])
    def options(self, request, pk=None):
        question = self.get_object()
        options = question.options.filter(is_deleted=False)
        serializer = QuestionOptionSerializer(options, many=True)
        return Response(serializer.data)


class QuestionOptionViewSet(viewsets.ModelViewSet):
    queryset = QuestionOption.objects.all()
    serializer_class = QuestionOptionDetailSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["question", "is_correct"]
    search_fields = ["option_text"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class TestAttemptViewSet(viewsets.ModelViewSet):
    queryset = TestAttempt.objects.all()
    serializer_class = TestAttemptSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["student", "test", "is_completed"]
    ordering_fields = ["started_at", "completed_at"]
    ordering = ["-started_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["get"])
    def answers(self, request, pk=None):
        attempt = self.get_object()
        answers = attempt.answers.filter(is_deleted=False)
        serializer = StudentAnswerSerializer(answers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        attempt = self.get_object()
        attempt.is_completed = True
        attempt.save()
        serializer = self.get_serializer(attempt)
        return Response(serializer.data)


class StudentAnswerViewSet(viewsets.ModelViewSet):
    queryset = StudentAnswer.objects.all()
    serializer_class = StudentAnswerSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["attempt", "question", "is_correct"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class TestResultViewSet(viewsets.ModelViewSet):
    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["student", "test", "is_passed", "is_published"]
    ordering_fields = ["percentage", "created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["get"])
    def section_results(self, request, pk=None):
        result = self.get_object()
        section_results = result.section_results.filter(is_deleted=False)
        serializer = SectionResultSerializer(section_results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        result = self.get_object()
        result.is_published = True
        result.save()
        serializer = self.get_serializer(result)
        return Response(serializer.data)


class SectionResultViewSet(viewsets.ModelViewSet):
    queryset = SectionResult.objects.all()
    serializer_class = SectionResultSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["result", "section", "is_checked"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def perform_update(self, serializer):
        serializer.save()


class ManualEvaluationViewSet(viewsets.ModelViewSet):
    queryset = ManualEvaluation.objects.all()
    serializer_class = ManualEvaluationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["answer", "checked_by", "is_final"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, checked_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class BandScoreMappingViewSet(viewsets.ModelViewSet):
    queryset = BandScoreMapping.objects.all()
    serializer_class = BandScoreMappingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomDefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["test_type", "section"]
    ordering_fields = ["min_score", "band_score"]
    ordering = ["min_score"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
