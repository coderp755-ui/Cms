from django.contrib import admin
from apps.classes.models import Course, Section, Lesson, LessonProgress


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'course_type', 'branch', 'is_active', 'created_at']
    list_filter = ['course_type', 'branch', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'is_active']
    list_filter = ['name', 'is_active', 'course__branch']
    search_fields = ['name', 'course__title']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'order', 'is_active']
    list_filter = ['is_active', 'section__course__branch']
    search_fields = ['title', 'content']
    ordering = ['section', 'order']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'is_completed', 'completed_at']
    list_filter = ['is_completed', 'user__branch', 'completed_at']
    search_fields = ['user__username', 'lesson__title']
    ordering = ['-created_at']

