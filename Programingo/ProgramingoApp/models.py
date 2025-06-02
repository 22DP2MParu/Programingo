import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from cloudinary.models import CloudinaryField

class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['order']


class TheoryPage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='theory_pages')
    order = models.PositiveIntegerField(default=1)
    content = models.TextField()

    class Meta:
        ordering = ['order']
        verbose_name = "Theory Page"
        verbose_name_plural = "Theory Pages"

    def __str__(self):
        return f"Theory Page {self.order} – {self.lesson.title}"


class Question(models.Model):
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('type_in', 'Type-in'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')


    def __str__(self):
        return f"Question: {self.text[:50]}"


class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        status = "(correct)" if self.is_correct else ""
        return f"Answer: {self.text[:50]} {status}"

class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    points = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} - {'Done' if self.completed else 'In Progress'}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    hearts = models.IntegerField(default=5)
    last_heart_update = models.DateTimeField(default=timezone.now)
    total_points = models.PositiveIntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    last_lesson_date = models.DateField(null=True, blank=True)
    coins = models.IntegerField(default=0)
    avatar = CloudinaryField('image', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"
    
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()


class DailyChallenge(models.Model):
    CHALLENGE_TYPES = [
        ('points', 'Earn Points'),
        ('lessons', 'Complete Lessons'),
        ('perfect', 'Perfect Accuracy'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES)
    target_value = models.IntegerField()
    reward_coins = models.IntegerField()
    active_date = models.DateField()

    def __str__(self):
        return f"{self.title} ({self.active_date})"
    
    
class UserChallengeProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    challenge = models.ForeignKey('DailyChallenge', on_delete=models.CASCADE)

    progress = models.PositiveIntegerField(default=0)  # Tracks current progress
    completed = models.BooleanField(default=False)     # Whether the challenge is completed
    rewarded = models.BooleanField(default=False)      # Whether reward has been claimed
    completed_at = models.DateTimeField(null=True, blank=True)  # When the challenge was completed

    class Meta:
        unique_together = ('user', 'challenge')

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"
    

class TrainingModule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class TrainingQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training = models.ForeignKey(TrainingModule, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()

    def __str__(self):
        return f"Question: {self.text[:50]}"


class TrainingAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(TrainingQuestion, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        status = "(correct)" if self.is_correct else ""
        return f"Answer: {self.text[:50]} {status}"


class TrainingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    training = models.ForeignKey(TrainingModule, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    earned_heart = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'training')

    def __str__(self):
        return f"{self.user.username} - {self.training.title} - {'Done' if self.completed else 'In Progress'}"
