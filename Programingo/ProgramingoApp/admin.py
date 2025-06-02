import nested_admin
from django.contrib import admin
from .models import Lesson, TheoryPage, Question, Answer, TrainingModule, TrainingQuestion, TrainingAnswer

# Inline for Answer inside Question
class AnswerInline(nested_admin.NestedTabularInline):
    model = Answer
    extra = 2

# Inline for Question inside Lesson
class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    extra = 1
    inlines = [AnswerInline]
    fields = ['text', 'question_type']

# Inline for TheoryPage inside Lesson
class TheoryPageInline(nested_admin.NestedStackedInline):
    model = TheoryPage
    extra = 1
    fields = ['order', 'content']

# Final Lesson admin with full nesting
class LessonAdmin(nested_admin.NestedModelAdmin):
    inlines = [TheoryPageInline, QuestionInline]
    list_display = ['title']

# Inline for TrainingAnswer inside TrainingQuestion
class TrainingAnswerInline(nested_admin.NestedTabularInline):
    model = TrainingAnswer
    extra = 2

# Inline for TrainingQuestion inside TrainingModule
class TrainingQuestionInline(nested_admin.NestedStackedInline):
    model = TrainingQuestion
    extra = 1
    inlines = [TrainingAnswerInline]
    fields = ['text']

# Final TrainingModule admin with nested questions and answers
class TrainingModuleAdmin(nested_admin.NestedModelAdmin):
    inlines = [TrainingQuestionInline]
    list_display = ['title']

admin.site.register(Lesson, LessonAdmin)

admin.site.register(TrainingModule, TrainingModuleAdmin)
