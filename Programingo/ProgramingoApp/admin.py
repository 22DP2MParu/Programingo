import nested_admin
from django.contrib import admin
from .models import Lesson, TheoryPage, Question, Answer

# Inline for Answer inside Question
class AnswerInline(nested_admin.NestedTabularInline):
    model = Answer
    extra = 2

# Inline for Question inside Lesson
class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    extra = 1
    inlines = [AnswerInline]
    fields = ['text']

# Inline for TheoryPage inside Lesson
class TheoryPageInline(nested_admin.NestedStackedInline):
    model = TheoryPage
    extra = 1
    fields = ['order', 'content']

# Final Lesson admin with full nesting
class LessonAdmin(nested_admin.NestedModelAdmin):
    inlines = [TheoryPageInline, QuestionInline]
    list_display = ['title']

# Register Lesson only (others will be edited via inlines)
admin.site.register(Lesson, LessonAdmin)
