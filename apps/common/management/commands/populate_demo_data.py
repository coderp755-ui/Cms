from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random

from apps.acounts.models import User, StudentProfile, TeacherProfile, Branch
from apps.classes.models import Course, Section, Lesson, LessonProgress
from apps.tests.models import (
    Test,
    TestSection,
    Question,
    QuestionOption,
    TestAttempt,
    StudentAnswer,
    TestResult,
    BandScoreMapping,
)


class Command(BaseCommand):
    help = "Populate database with demo/test data for all models"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting demo data population..."))

        # Create branches first
        self.create_branches()

        # Create users
        self.create_users()

        # Create courses and sections
        self.create_courses()

        # Create lessons
        self.create_lessons()

        # Create tests
        self.create_tests()

        # Create test attempts and results
        self.create_test_attempts()

        # Create band score mappings
        self.create_band_mappings()

        # Create lesson progress
        self.create_lesson_progress()

        self.stdout.write(self.style.SUCCESS("✓ Demo data populated successfully!"))

    def create_branches(self):
        self.stdout.write("Creating branches...")

        branch_data = [
            {
                "name": "Kathmandu Branch",
                "code": "KTM",
                "address": "Thamel, Kathmandu",
                "phone": "+977-1-4123456",
                "email": "ktm@grace.edu.np",
            },
            {
                "name": "Pokhara Branch",
                "code": "PKR",
                "address": "Lakeside, Pokhara",
                "phone": "+977-61-123456",
                "email": "pkr@grace.edu.np",
            },
            {
                "name": "Lalitpur Branch",
                "code": "LTP",
                "address": "Jawalakhel, Lalitpur",
                "phone": "+977-1-5123456",
                "email": "ltp@grace.edu.np",
            },
        ]

        self.branches = []
        for data in branch_data:
            branch, created = Branch.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "address": data["address"],
                    "phone": data["phone"],
                    "email": data["email"],
                    "is_active": True,
                },
            )
            self.branches.append(branch)
            if created:
                self.stdout.write(f"  ✓ Created branch: {branch.name} ({branch.code})")
            else:
                self.stdout.write(f"  → Branch already exists: {branch.name}")

    def create_users(self):
        self.stdout.write("Creating users...")

        # Create superadmin (no branch needed)
        if not User.objects.filter(username="superadmin").exists():
            superadmin = User.objects.create_superuser(
                username="superadmin",
                email="superadmin@test.com",
                password="admin123",
                role="superadmin",
                is_super=True,
                first_name="Super",
                last_name="Admin",
            )
            self.stdout.write(f"  ✓ Created superadmin: {superadmin.username}")

        # Create admins for each branch
        for idx, branch in enumerate(self.branches, 1):
            username = f"admin{idx}"
            if not User.objects.filter(username=username).exists():
                admin = User.objects.create_user(
                    username=username,
                    email=f"admin{idx}@test.com",
                    password="admin123",
                    role="admin",
                    branch=branch,
                    first_name="Admin",
                    last_name=f"{branch.name.split()[0]}",
                )
                self.stdout.write(
                    f"  ✓ Created admin: {admin.username} for {branch.name}"
                )

        # Create teachers for each branch
        teacher_data = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "dept": "IELTS",
                "subject": "Speaking & Writing",
            },
            {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "dept": "PTE",
                "subject": "Reading & Listening",
            },
            {
                "first_name": "Michael",
                "last_name": "Brown",
                "dept": "IELTS",
                "subject": "All Sections",
            },
        ]

        teacher_count = 1
        for branch in self.branches:
            for data in teacher_data[:2]:  # 2 teachers per branch
                username = f"teacher{teacher_count}"
                if not User.objects.filter(username=username).exists():
                    teacher = User.objects.create_user(
                        username=username,
                        email=f"teacher{teacher_count}@test.com",
                        password="teacher123",
                        role="teacher",
                        branch=branch,
                        first_name=data["first_name"],
                        last_name=data["last_name"],
                    )

                    TeacherProfile.objects.create(
                        user=teacher,
                        department=data["dept"],
                        subject_specialization=data["subject"],
                        qualification="Master in English Literature",
                        experience_years=random.randint(3, 10),
                        hire_date=date.today()
                        - timedelta(days=random.randint(365, 1825)),
                        salary=Decimal(random.randint(50000, 80000)),
                        employment_type="full_time",
                        subjects_teaching=data["subject"],
                    )
                    self.stdout.write(
                        f"  ✓ Created teacher: {teacher.username} for {branch.name}"
                    )
                    teacher_count += 1

        # Create students for each branch
        student_data = [
            {"first_name": "Alice", "last_name": "Brown", "grade": "Grade 12"},
            {"first_name": "Bob", "last_name": "Wilson", "grade": "Grade 11"},
            {"first_name": "Charlie", "last_name": "Davis", "grade": "Grade 12"},
            {"first_name": "Diana", "last_name": "Miller", "grade": "Grade 10"},
            {"first_name": "Eve", "last_name": "Taylor", "grade": "Grade 11"},
        ]

        student_count = 1
        for branch in self.branches:
            for data in student_data[:3]:  # 3 students per branch
                username = f"student{student_count}"
                if not User.objects.filter(username=username).exists():
                    student = User.objects.create_user(
                        username=username,
                        email=f"student{student_count}@test.com",
                        password="student123",
                        role="student",
                        branch=branch,
                        first_name=data["first_name"],
                        last_name=data["last_name"],
                    )

                    StudentProfile.objects.create(
                        user=student,
                        grade_level=data["grade"],
                        roll_number=f"ROLL{random.randint(1000, 9999)}",
                        admission_date=date.today()
                        - timedelta(days=random.randint(30, 365)),
                        father_name=f"{data['first_name']}'s Father",
                        mother_name=f"{data['first_name']}'s Mother",
                        guardian_phone=f"+977-98{random.randint(10000000, 99999999)}",
                        guardian_email=f"guardian_{username}@test.com",
                    )
                    self.stdout.write(
                        f"  ✓ Created student: {student.username} for {branch.name}"
                    )
                    student_count += 1

    def create_courses(self):
        self.stdout.write("Creating courses and sections...")

        course_data = [
            {
                "title": "IELTS Academic Preparation",
                "description": "Complete IELTS Academic preparation course covering all four sections",
                "course_type": "IELTS",
            },
            {
                "title": "IELTS General Training",
                "description": "IELTS General Training course for immigration and work purposes",
                "course_type": "IELTS",
            },
            {
                "title": "PTE Academic Complete",
                "description": "Comprehensive PTE Academic preparation course",
                "course_type": "PTE",
            },
        ]

        # Create courses for each branch
        for branch in self.branches:
            for data in course_data:
                title = f"{data['title']} - {branch.code}"
                course, created = Course.objects.get_or_create(
                    title=title,
                    course_type=data["course_type"],
                    branch=branch,
                    defaults={"description": data["description"]},
                )

                if created:
                    self.stdout.write(f"  ✓ Created course: {course.title}")

                    # Create sections for each course
                    for section_name in ["listening", "reading", "writing", "speaking"]:
                        Section.objects.get_or_create(course=course, name=section_name)
                    self.stdout.write(f"    ✓ Created 4 sections for {course.title}")

                    # Enroll students from the same branch
                    students = User.objects.filter(role="student", branch=branch)
                    for student in students:
                        student.enrolled_courses.add(course)
                    self.stdout.write(
                        f"    ✓ Enrolled {students.count()} students in {course.title}"
                    )

    def create_lessons(self):
        self.stdout.write("Creating lessons...")

        sections = Section.objects.all()

        lesson_templates = {
            "listening": [
                "Introduction to Listening Section",
                "Note-taking Strategies",
                "Multiple Choice Questions",
                "Form Completion Practice",
                "Map and Diagram Labeling",
            ],
            "reading": [
                "Reading Strategies Overview",
                "Skimming and Scanning Techniques",
                "True/False/Not Given Questions",
                "Matching Headings",
                "Summary Completion",
            ],
            "writing": [
                "Task 1: Graph Description",
                "Task 1: Process Diagrams",
                "Task 2: Opinion Essays",
                "Task 2: Discussion Essays",
                "Grammar and Vocabulary",
            ],
            "speaking": [
                "Part 1: Introduction Questions",
                "Part 2: Cue Card Practice",
                "Part 3: Discussion Topics",
                "Pronunciation Tips",
                "Fluency Development",
            ],
        }

        for section in sections:
            templates = lesson_templates.get(section.name, [])
            for idx, title in enumerate(templates, 1):
                lesson, created = Lesson.objects.get_or_create(
                    section=section,
                    order=idx,
                    defaults={
                        "title": title,
                        "content": f"This is the content for {title}. It includes detailed explanations, examples, and practice exercises.",
                        "video_url": f"https://www.youtube.com/watch?v=example{idx}",
                    },
                )
                if created:
                    self.stdout.write(f"  ✓ Created lesson: {lesson.title}")

    def create_tests(self):
        self.stdout.write("Creating tests...")

        courses = Course.objects.all()

        for course in courses:
            # Create Mock Test
            test, created = Test.objects.get_or_create(
                course=course,
                title=f"{course.course_type} Full Mock Test 1",
                defaults={
                    "description": f"Complete {course.course_type} mock test with all sections",
                    "test_kind": "mock",
                    "duration_minutes": 180,
                    "total_marks": 40,
                },
            )

            if created:
                self.stdout.write(f"  ✓ Created test: {test.title}")
                self.create_test_sections_and_questions(test)

            # Create Practice Test
            practice_test, created = Test.objects.get_or_create(
                course=course,
                title=f"{course.course_type} Practice Test - Reading",
                defaults={
                    "description": "Practice test focusing on reading section",
                    "test_kind": "practice",
                    "duration_minutes": 60,
                    "total_marks": 40,
                },
            )

            if created:
                self.stdout.write(f"  ✓ Created practice test: {practice_test.title}")

    def create_test_sections_and_questions(self, test):
        sections = Section.objects.filter(course=test.course)

        for section in sections:
            test_section, created = TestSection.objects.get_or_create(
                test=test,
                section=section,
                defaults={"duration_minutes": 45, "total_marks": 10},
            )

            if created:
                # Create questions for each section
                question_types = ["mcq", "text"]
                for i in range(1, 6):  # 5 questions per section
                    q_type = random.choice(question_types)
                    question = Question.objects.create(
                        test_section=test_section,
                        question_text=f"Question {i} for {section.name} section",
                        question_type=q_type,
                        marks=2,
                        order=i,
                        correct_answer="Sample correct answer"
                        if q_type == "text"
                        else None,
                    )

                    # Create options for MCQ
                    if q_type == "mcq":
                        options = ["Option A", "Option B", "Option C", "Option D"]
                        for idx, opt in enumerate(options):
                            QuestionOption.objects.create(
                                question=question,
                                option_text=opt,
                                is_correct=(idx == 0),  # First option is correct
                            )

    def create_test_attempts(self):
        self.stdout.write("Creating test attempts and results...")

        students = User.objects.filter(role="student")
        tests = Test.objects.filter(test_kind="mock")[:2]  # First 2 mock tests

        for student in students[:2]:  # First 2 students
            for test in tests:
                attempt, created = TestAttempt.objects.get_or_create(
                    student=student,
                    test=test,
                    defaults={
                        "started_at": timezone.now()
                        - timedelta(days=random.randint(1, 30)),
                        "completed_at": timezone.now()
                        - timedelta(days=random.randint(1, 30)),
                        "is_completed": True,
                    },
                )

                if created:
                    self.stdout.write(
                        f"  ✓ Created attempt: {student.username} - {test.title}"
                    )

                    # Create answers
                    questions = Question.objects.filter(test_section__test=test)
                    total_marks = 0
                    obtained_marks = 0

                    for question in questions:
                        is_correct = random.choice([True, False, True])  # 66% correct
                        marks = question.marks if is_correct else 0

                        answer_data = {
                            "attempt": attempt,
                            "question": question,
                            "marks_obtained": marks,
                            "is_correct": is_correct,
                        }

                        if question.question_type == "mcq":
                            correct_option = question.options.filter(
                                is_correct=True
                            ).first()
                            answer_data["selected_option"] = (
                                correct_option
                                if is_correct
                                else question.options.exclude(is_correct=True).first()
                            )
                        else:
                            answer_data["answer_text"] = "Student answer text here"

                        StudentAnswer.objects.create(**answer_data)

                        total_marks += question.marks
                        obtained_marks += marks

                    # Create test result
                    percentage = (
                        (obtained_marks / total_marks * 100) if total_marks > 0 else 0
                    )
                    band_score = self.calculate_band_score(percentage)

                    TestResult.objects.create(
                        attempt=attempt,
                        student=student,
                        test=test,
                        total_marks=total_marks,
                        obtained_marks=obtained_marks,
                        percentage=Decimal(percentage).quantize(Decimal("0.01")),
                        band_score=band_score,
                        is_passed=percentage >= 60,
                        is_published=True,
                    )
                    self.stdout.write(
                        f"    ✓ Created result: {obtained_marks}/{total_marks} ({percentage:.1f}%)"
                    )

    def calculate_band_score(self, percentage):
        """Calculate IELTS band score from percentage"""
        if percentage >= 90:
            return Decimal("9.0")
        elif percentage >= 80:
            return Decimal("8.0")
        elif percentage >= 70:
            return Decimal("7.0")
        elif percentage >= 60:
            return Decimal("6.0")
        elif percentage >= 50:
            return Decimal("5.0")
        else:
            return Decimal("4.0")

    def create_band_mappings(self):
        self.stdout.write("Creating band score mappings...")

        mappings = [
            # IELTS Listening
            {
                "test_type": "IELTS",
                "section": "listening",
                "min_score": 39,
                "max_score": 40,
                "band_score": Decimal("9.0"),
            },
            {
                "test_type": "IELTS",
                "section": "listening",
                "min_score": 35,
                "max_score": 38,
                "band_score": Decimal("8.0"),
            },
            {
                "test_type": "IELTS",
                "section": "listening",
                "min_score": 30,
                "max_score": 34,
                "band_score": Decimal("7.0"),
            },
            {
                "test_type": "IELTS",
                "section": "listening",
                "min_score": 23,
                "max_score": 29,
                "band_score": Decimal("6.0"),
            },
            # IELTS Reading
            {
                "test_type": "IELTS",
                "section": "reading",
                "min_score": 39,
                "max_score": 40,
                "band_score": Decimal("9.0"),
            },
            {
                "test_type": "IELTS",
                "section": "reading",
                "min_score": 35,
                "max_score": 38,
                "band_score": Decimal("8.0"),
            },
            {
                "test_type": "IELTS",
                "section": "reading",
                "min_score": 30,
                "max_score": 34,
                "band_score": Decimal("7.0"),
            },
            {
                "test_type": "IELTS",
                "section": "reading",
                "min_score": 23,
                "max_score": 29,
                "band_score": Decimal("6.0"),
            },
        ]

        for mapping in mappings:
            obj, created = BandScoreMapping.objects.get_or_create(**mapping)
            if created:
                self.stdout.write(
                    f"  ✓ Created mapping: {mapping['section']} {mapping['min_score']}-{mapping['max_score']} → {mapping['band_score']}"
                )

    def create_lesson_progress(self):
        self.stdout.write("Creating lesson progress...")

        students = User.objects.filter(role="student")
        lessons = Lesson.objects.all()[:10]  # First 10 lessons

        for student in students[:2]:  # First 2 students
            for lesson in lessons[:5]:  # Complete first 5 lessons
                progress, created = LessonProgress.objects.get_or_create(
                    user=student,
                    lesson=lesson,
                    defaults={
                        "is_completed": True,
                        "completed_at": timezone.now()
                        - timedelta(days=random.randint(1, 20)),
                    },
                )
                if created:
                    self.stdout.write(
                        f"  ✓ Progress: {student.username} completed {lesson.title}"
                    )
