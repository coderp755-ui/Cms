from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random

from apps.acounts.models import User, StudentProfile, TeacherProfile, Branch
from apps.classes.models import Course, Section, Lesson
from apps.tests.models import (
    Test, TestSection, Question, QuestionOption, TestAttempt,
    StudentAnswer, TestResult
)


class Command(BaseCommand):
    help = 'Populate database with bulk test data for load testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--students',
            type=int,
            default=100,
            help='Number of students to create (default: 100)'
        )
        parser.add_argument(
            '--teachers',
            type=int,
            default=10,
            help='Number of teachers to create (default: 10)'
        )
        parser.add_argument(
            '--tests-per-course',
            type=int,
            default=5,
            help='Number of tests per course (default: 5)'
        )

    def handle(self, *args, **options):
        num_students = options['students']
        num_teachers = options['teachers']
        tests_per_course = options['tests_per_course']
        
        self.stdout.write(self.style.SUCCESS('Starting bulk data population...'))
        self.stdout.write(f'  Students: {num_students}')
        self.stdout.write(f'  Teachers: {num_teachers}')
        self.stdout.write(f'  Tests per course: {tests_per_course}')
        
        # Ensure branches exist
        self.ensure_branches()
        
        # Create bulk users
        self.create_bulk_teachers(num_teachers)
        self.create_bulk_students(num_students)
        
        # Ensure courses exist
        self.ensure_courses()
        
        # Create bulk tests
        self.create_bulk_tests(tests_per_course)
        
        # Create test attempts for students
        self.create_bulk_test_attempts()
        
        self.stdout.write(self.style.SUCCESS('✓ Bulk data populated successfully!'))
        self.print_summary()

    def ensure_branches(self):
        self.stdout.write('Ensuring branches exist...')
        
        branch_data = [
            {'name': 'Kathmandu Branch', 'code': 'KTM', 'address': 'Thamel, Kathmandu'},
            {'name': 'Pokhara Branch', 'code': 'PKR', 'address': 'Lakeside, Pokhara'},
            {'name': 'Lalitpur Branch', 'code': 'LTP', 'address': 'Jawalakhel, Lalitpur'},
        ]
        
        self.branches = []
        for data in branch_data:
            branch, created = Branch.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'address': data['address'],
                    'is_active': True
                }
            )
            self.branches.append(branch)

    def create_bulk_teachers(self, count):
        self.stdout.write(f'Creating {count} teachers...')
        
        existing_count = User.objects.filter(role='teacher').count()
        
        departments = ['IELTS', 'PTE', 'General English']
        subjects = ['Speaking & Writing', 'Reading & Listening', 'All Sections']
        
        created = 0
        for i in range(existing_count + 1, existing_count + count + 1):
            username = f'teacher{i}'
            
            if User.objects.filter(username=username).exists():
                continue
            
            branch = random.choice(self.branches)
            
            teacher = User.objects.create_user(
                username=username,
                email=f'teacher{i}@test.com',
                password='teacher123',
                role='teacher',
                branch=branch,
                first_name='Teacher',
                last_name=f'{i}'
            )
            
            # Only create profile if it doesn't exist
            if not hasattr(teacher, 'teacherprofile'):
                TeacherProfile.objects.create(
                    user=teacher,
                    employee_code=f'EMP{10000 + i}',
                    department=random.choice(departments),
                    subject_specialization=random.choice(subjects),
                    qualification='Master in English Literature',
                    experience_years=random.randint(2, 15),
                    hire_date=date.today() - timedelta(days=random.randint(365, 2000)),
                    salary=Decimal(random.randint(40000, 90000)),
                    employment_type='full_time'
                )
            created += 1
            
            if created % 10 == 0:
                self.stdout.write(f'  Created {created} teachers...')
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {created} teachers'))

    def create_bulk_students(self, count):
        self.stdout.write(f'Creating {count} students...')
        
        existing_count = User.objects.filter(role='student').count()
        
        grades = ['Grade 10', 'Grade 11', 'Grade 12', 'Bachelor']
        
        created = 0
        for i in range(existing_count + 1, existing_count + count + 1):
            username = f'student{i}'
            
            if User.objects.filter(username=username).exists():
                continue
            
            branch = random.choice(self.branches)
            
            student = User.objects.create_user(
                username=username,
                email=f'student{i}@test.com',
                password='student123',
                role='student',
                branch=branch,
                first_name='Student',
                last_name=f'{i}'
            )
            
            # Only create profile if it doesn't exist
            if not hasattr(student, 'studentprofile'):
                StudentProfile.objects.create(
                    user=student,
                    grade_level=random.choice(grades),
                    roll_number=f"ROLL{10000 + i}",
                    admission_date=date.today() - timedelta(days=random.randint(30, 730)),
                    father_name=f"Father {i}",
                    mother_name=f"Mother {i}",
                    guardian_phone=f"+977-98{random.randint(10000000, 99999999)}",
                    guardian_email=f"guardian{i}@test.com",
                )
            
            # Enroll in random courses from their branch
            courses = Course.objects.filter(branch=branch)
            if courses.exists():
                num_courses = random.randint(1, min(2, courses.count()))
                enrolled = random.sample(list(courses), num_courses)
                student.enrolled_courses.set(enrolled)
            
            created += 1
            
            if created % 50 == 0:
                self.stdout.write(f'  Created {created} students...')
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {created} students'))

    def ensure_courses(self):
        self.stdout.write('Ensuring courses exist...')
        
        course_data = [
            {'title': 'IELTS Academic Preparation', 'type': 'IELTS'},
            {'title': 'PTE Academic Complete', 'type': 'PTE'},
        ]
        
        for branch in self.branches:
            for data in course_data:
                title = f"{data['title']} - {branch.code}"
                course, created = Course.objects.get_or_create(
                    title=title,
                    course_type=data['type'],
                    branch=branch,
                    defaults={'description': f"Complete {data['type']} preparation course"}
                )
                
                if created:
                    # Create sections
                    for section_name in ['listening', 'reading', 'writing', 'speaking']:
                        Section.objects.get_or_create(course=course, name=section_name)

    def create_bulk_tests(self, tests_per_course):
        self.stdout.write(f'Creating {tests_per_course} tests per course...')
        
        courses = Course.objects.all()
        test_kinds = ['mock', 'practice', 'sectional']
        
        created = 0
        for course in courses:
            for i in range(1, tests_per_course + 1):
                test_kind = test_kinds[i % len(test_kinds)]
                title = f'{course.course_type} {test_kind.title()} Test {i} - {course.branch.code}'
                
                test, test_created = Test.objects.get_or_create(
                    course=course,
                    title=title,
                    defaults={
                        'description': f'{test_kind.title()} test for {course.course_type}',
                        'test_kind': test_kind,
                        'duration_minutes': 180 if test_kind == 'mock' else 60,
                        'total_marks': 40
                    }
                )
                
                if test_created:
                    self.create_test_content(test)
                    created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {created} tests'))

    def create_test_content(self, test):
        """Create sections and questions for a test"""
        sections = Section.objects.filter(course=test.course)
        
        for section in sections:
            test_section, created = TestSection.objects.get_or_create(
                test=test,
                section=section,
                defaults={
                    'duration_minutes': 45,
                    'total_marks': 10
                }
            )
            
            if created:
                # Create 10 questions per section
                for i in range(1, 11):
                    q_type = 'mcq' if i <= 7 else 'text'
                    question = Question.objects.create(
                        test_section=test_section,
                        question_text=f'Question {i} for {section.name}',
                        question_type=q_type,
                        marks=1,
                        order=i,
                        correct_answer='Correct answer' if q_type == 'text' else None
                    )
                    
                    if q_type == 'mcq':
                        for idx, opt in enumerate(['A', 'B', 'C', 'D']):
                            QuestionOption.objects.create(
                                question=question,
                                option_text=f'Option {opt}',
                                is_correct=(idx == 0)
                            )

    def create_bulk_test_attempts(self):
        self.stdout.write('Creating test attempts...')
        
        students = User.objects.filter(role='student')
        tests = Test.objects.all()
        
        # Each student attempts 2-3 random tests
        created = 0
        for student in students:
            available_tests = tests.filter(course__branch=student.branch)
            if not available_tests.exists():
                continue
            
            num_attempts = random.randint(2, min(3, available_tests.count()))
            selected_tests = random.sample(list(available_tests), num_attempts)
            
            for test in selected_tests:
                if TestAttempt.objects.filter(student=student, test=test).exists():
                    continue
                
                attempt = TestAttempt.objects.create(
                    student=student,
                    test=test,
                    started_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                    is_completed=True
                )
                
                # Create answers
                questions = Question.objects.filter(test_section__test=test)
                total_marks = 0
                obtained_marks = 0
                
                for question in questions:
                    is_correct = random.random() > 0.3  # 70% correct rate
                    marks = question.marks if is_correct else 0
                    
                    answer_data = {
                        'attempt': attempt,
                        'question': question,
                        'marks_obtained': marks,
                        'is_correct': is_correct
                    }
                    
                    if question.question_type == 'mcq':
                        if is_correct:
                            answer_data['selected_option'] = question.options.filter(is_correct=True).first()
                        else:
                            answer_data['selected_option'] = question.options.filter(is_correct=False).first()
                    else:
                        answer_data['answer_text'] = 'Student answer'
                    
                    StudentAnswer.objects.create(**answer_data)
                    total_marks += question.marks
                    obtained_marks += marks
                
                # Create result
                percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
                band_score = self.calculate_band_score(percentage)
                
                TestResult.objects.create(
                    attempt=attempt,
                    student=student,
                    test=test,
                    total_marks=total_marks,
                    obtained_marks=obtained_marks,
                    percentage=Decimal(percentage).quantize(Decimal('0.01')),
                    band_score=band_score,
                    is_passed=percentage >= 60,
                    is_published=True
                )
                
                created += 1
                
                if created % 100 == 0:
                    self.stdout.write(f'  Created {created} attempts...')
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {created} test attempts'))

    def calculate_band_score(self, percentage):
        if percentage >= 90:
            return Decimal('9.0')
        elif percentage >= 80:
            return Decimal('8.0')
        elif percentage >= 70:
            return Decimal('7.0')
        elif percentage >= 60:
            return Decimal('6.0')
        elif percentage >= 50:
            return Decimal('5.0')
        else:
            return Decimal('4.0')

    def print_summary(self):
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('DATABASE SUMMARY'))
        self.stdout.write('='*50)
        
        self.stdout.write(f'Branches: {Branch.objects.count()}')
        self.stdout.write('Users:')
        self.stdout.write(f'  - Superadmins: {User.objects.filter(role="superadmin").count()}')
        self.stdout.write(f'  - Admins: {User.objects.filter(role="admin").count()}')
        self.stdout.write(f'  - Teachers: {User.objects.filter(role="teacher").count()}')
        self.stdout.write(f'  - Students: {User.objects.filter(role="student").count()}')
        self.stdout.write(f'Courses: {Course.objects.count()}')
        self.stdout.write(f'Sections: {Section.objects.count()}')
        self.stdout.write(f'Lessons: {Lesson.objects.count()}')
        self.stdout.write(f'Tests: {Test.objects.count()}')
        self.stdout.write(f'Questions: {Question.objects.count()}')
        self.stdout.write(f'Test Attempts: {TestAttempt.objects.count()}')
        self.stdout.write(f'Test Results: {TestResult.objects.count()}')
        self.stdout.write('='*50 + '\n')
