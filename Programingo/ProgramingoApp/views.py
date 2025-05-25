from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import CustomLoginForm, CustomRegistrationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.utils import timezone
from .models import Lesson, LessonProgress
from .models import UserProfile, Question, Answer, DailyChallenge, UserChallengeProgress
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from datetime import timedelta
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.core.management.base import BaseCommand


from .models import Lesson
from .models import Answer


def welcome(request):
    return render(request, 'welcome.html')

def home(request):
    lessons = Lesson.objects.all()
    completed_lessons_ids = set()

    if request.user.is_authenticated:
        profile = request.user.profile
        reset_hearts_if_needed(profile)
        try:
            completed_lessons_ids = set(
                LessonProgress.objects.filter(user=request.user, completed__exact=True)
                .values_list('lesson_id', flat=True)
            )
        except Exception:
            # Fallback to manual filtering if Djongo fails
            progresses = LessonProgress.objects.filter(user=request.user)
            completed_lessons_ids = set(p.lesson_id for p in progresses if p.completed)

    return render(request, 'home.html', {
        'lessons': lessons,
        'completed_lessons_ids': completed_lessons_ids,
    })

def training(request):
    return render(request, 'training.html')

def leagues(request):
    return render(request, 'leagues.html')

def challenges(request):
    return render(request, 'challenges.html')

def shop(request):
    return render(request, 'shop.html')

def profile(request):
    return render(request, 'profile.html')

def custom_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Find the user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                form.add_error('email', 'No account found with this email.')
                return render(request, 'login.html', {'form': form})

            # Authenticate by username and password
            user = authenticate(username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error('password', 'Incorrect password.')
    else:
        form = CustomLoginForm()
    return render(request, 'login.html', {'form': form})


def register(request):
    if request.method == "POST":
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Check if username already exists
            if User.objects.filter(username=name).exists():
                form.add_error('name', "This username is already taken.")
                return render(request, "register.html", {"form": form})

            user = User.objects.create_user(username=name, email=email, password=password)
            user.save()
            return redirect("login")
        else:
            return render(request, "register.html", {"form": form})
    else:
        form = CustomRegistrationForm()
        return render(request, "register.html", {"form": form})
    

def lesson_page(request, lesson_id, page):
    lesson = get_object_or_404(Lesson, id=lesson_id)

        # Check if user completed the lesson
    if request.user.is_authenticated:
        try:
            progress = LessonProgress.objects.get(user=request.user, lesson=lesson)
            if progress.completed:
                return render(request, 'lesson/completed.html', {
                    'lesson': lesson,
                })
        except LessonProgress.DoesNotExist:
            pass

    theory_pages = list(lesson.theory_pages.all())
    questions = list(lesson.questions.all())

    theory_count = len(theory_pages)
    question_count = len(questions)
    total_pages = theory_count + question_count

    # Start session timer
    if page == 1:
        request.session['lesson_start_time'] = timezone.now().isoformat()

    # Default to 0 progress
    progress_percent = 0
    current_question_number = 0

    # Handle theory pages
    if 1 <= page <= theory_count:
        theory = theory_pages[page - 1]
        return render(request, 'lesson/theory.html', {
            'lesson': lesson,
            'theory': theory,
            'page': page,
            'total_pages': total_pages,
            'progress_percent': progress_percent,
        })

    # Handle question pages
    if theory_count < page <= total_pages:
        question_index = page - theory_count - 1
        question = questions[question_index]
        current_question_number = question_index + 1

        if request.method == 'POST':
            selected_choice_id = request.POST.get('answer')
            if selected_choice_id:
                answers = request.session.get(f'lesson_{lesson_id}_answers', {})
                answers[str(question.id)] = selected_choice_id
                request.session[f'lesson_{lesson_id}_answers'] = answers

                # Check if selected answer is correct
                selected_answer = Answer.objects.filter(id=selected_choice_id, question=question).first()
                is_correct = selected_answer.is_correct if selected_answer else False

                # Deduct heart if wrong
                if not is_correct and request.user.is_authenticated:
                    profile, _ = UserProfile.objects.get_or_create(user=request.user)
                    if profile.hearts > 0:
                        profile.hearts -= 1
                        profile.save()

            # Update progress AFTER answering
            progress_percent = int((current_question_number / question_count) * 100)

            if page == total_pages:
                return redirect('lesson_result', lesson_id=lesson.id)
            else:
                return redirect('lesson_page', lesson_id=lesson.id, page=page + 1)

        # On GET (not answered yet), keep progress at last answered
        # So don't increment until after post
        answered_count = len(request.session.get(f'lesson_{lesson_id}_answers', {}))
        progress_percent = int((answered_count / question_count) * 100)

        user_hearts = None
        if request.user.is_authenticated:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            user_hearts = profile.hearts

        return render(request, 'lesson/question.html', {
            'lesson': lesson,
            'question': question,
            'page': page,
            'total_pages': total_pages,
            'progress_percent': progress_percent,
            'question_count': question_count,
            'current_question_number': current_question_number,
            'user_hearts': user_hearts,
            'out_of_hearts': request.user.is_authenticated and request.user.profile.hearts == 0,
        })

    return redirect('lesson_page', lesson_id=lesson.id, page=1)


def lesson_result(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    answers = request.session.get(f'lesson_{lesson_id}_answers', {})

    correct_count = 0
    total_questions = lesson.questions.count()
    for question in lesson.questions.all():
        user_answer = answers.get(str(question.id))
        if user_answer:
            try:
                selected_answer = Answer.objects.get(id=user_answer)
                if selected_answer.is_correct:
                    correct_count += 1
            except Answer.DoesNotExist:
                pass

    accuracy = 0
    if total_questions > 0:
        accuracy = round((correct_count / total_questions) * 100)

    # Calculate points based on accuracy
    if accuracy <= 15:
        points = 4
    elif accuracy <= 45:
        points = 6
    elif accuracy <= 90:
        points = 8
    else:  # 91-100%
        points = 10

    time_spent = request.session.get(f'lesson_{lesson_id}_final_time')
    if time_spent is None:
        start_time_str = request.session.get('lesson_start_time')
        if start_time_str:
            start_time = timezone.datetime.fromisoformat(start_time_str)
            time_spent = (timezone.now() - start_time).seconds
            request.session[f'lesson_{lesson_id}_final_time'] = time_spent
        else:
            time_spent = 0

    # Mark lesson as completed and save points in DB for this user
    if request.user.is_authenticated:
        # Update or create LessonProgress with points
        lesson_progress, created = LessonProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={
                'completed': True,
                'completed_at': timezone.now(),
                'points': points,
            }
        )

        # Update user's total points (add points from this lesson)
        profile = request.user.profile
        # To avoid double counting points if lesson was already completed, subtract old points if updating
        if not created:
            old_points = lesson_progress.points
            profile.total_points = profile.total_points - old_points + points
        else:
            profile.total_points += points

        # Update streak logic
        today = timezone.now().date()
        last_date = profile.last_lesson_date

        if last_date is None:
            profile.current_streak = 1
        else:
            if last_date == today:
                # Already completed lesson today — do nothing
                pass
            elif last_date == today - timedelta(days=1):
                profile.current_streak += 1
            else:
                profile.current_streak = 1  # streak broken, reset

        profile.last_lesson_date = today
        update_challenge_progress(request.user, points, created, accuracy)
        profile.save()

    return render(request, 'lesson/result.html', {
        'lesson': lesson,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'accuracy': accuracy,
        'time_spent': time_spent,
        'points': points, 
    })


def end_lesson(request, lesson_id):
    request.session.pop(f'lesson_{lesson_id}_answers', None)
    request.session.pop('lesson_start_time', None)
    request.session.pop(f'lesson_{lesson_id}_final_time', None)
    return redirect('home')

@require_POST
def check_answer(request):
    question_id = request.POST.get('question_id')
    answer_id = request.POST.get('answer_id')
    lesson_id = request.POST.get('lesson_id')

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=403)

    try:
        question = get_object_or_404(Question, id=question_id)
        answer = get_object_or_404(Answer, id=answer_id, question=question)
        is_correct = answer.is_correct
    except (Question.DoesNotExist, Answer.DoesNotExist):
        return JsonResponse({'error': 'Invalid question or answer.'}, status=400)

    # Update session answers
    answers = request.session.get(f'lesson_{lesson_id}_answers', {})
    answers[question_id] = answer_id
    request.session[f'lesson_{lesson_id}_answers'] = answers

    # Deduct heart if incorrect
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not is_correct:
        if profile.hearts > 0:
            profile.hearts -= 1
            profile.save()

    hearts = profile.hearts

    return JsonResponse({'correct': is_correct, 'hearts': hearts})


def leaderboard(request):
    users = User.objects.all()

    # Ranks won't be sorted due to Djongo issue with JOINs.
    users = sorted(users, key=lambda u: getattr(u.profile, 'total_points', 0), reverse=True)

    return render(request, 'leaderboard.html', {
        'users': users,
        'current_user': request.user
    })

def reset_hearts_if_needed(user_profile):
    now = timezone.now()
    if user_profile.hearts < 5:
        # Check if last update was more than 5 minutes ago
        if user_profile.last_heart_update is None or (now - user_profile.last_heart_update) >= timedelta(minutes=5):
            user_profile.hearts = min(user_profile.hearts + 1, 5)
            user_profile.last_heart_update = now
            user_profile.save()


def create_daily_challenges_if_needed():
    today = timezone.localdate()  # ensures current date in correct timezone

    print("Checking for existing challenges...")  # Debug
    existing = DailyChallenge.objects.filter(active_date=today)
    if existing.exists():
        print("Challenges already exist for today.")
        return

    print("Creating daily challenges for", today)  # Debug

    challenges = [
        {
            "title": "Earn 30 points",
            "description": "Earn at least 30 points today.",
            "challenge_type": "points",
            "target_value": 30,
            "reward_coins": 10,
        },
        {
            "title": "Complete 3 lessons",
            "description": "Finish 3 full lessons today.",
            "challenge_type": "lessons",
            "target_value": 3,
            "reward_coins": 20,
        },
        {
            "title": "Perfect accuracy",
            "description": "Finish a lesson with 100% accuracy.",
            "challenge_type": "perfect",
            "target_value": 1,
            "reward_coins": 15,
        },
    ]

    for challenge in challenges:
        DailyChallenge.objects.create(
            title=challenge["title"],
            description=challenge["description"],
            challenge_type=challenge["challenge_type"],
            target_value=challenge["target_value"],
            reward_coins=challenge["reward_coins"],
            active_date=today,
        )
        print(f"Created challenge: {challenge['title']}")  # Debug


def challenges_view(request):
    create_daily_challenges_if_needed()

    today = timezone.now().date()
    challenges = DailyChallenge.objects.filter(active_date=today)

    user_challenges = []
    if request.user.is_authenticated:
        for challenge in challenges:
            progress_obj, created = UserChallengeProgress.objects.get_or_create(
                user=request.user,
                challenge=challenge,
                defaults={
                    'progress': 0,
                    'completed': False,
                    'rewarded': False,
                    'completed_at': None,
                }
            )
            user_challenges.append(progress_obj)

    return render(request, 'challenges.html', {
        'user_challenges': user_challenges
    })

def update_challenge_progress(user, points_earned, lesson_completed, accuracy):
    today = now().date()
    challenges = DailyChallenge.objects.filter(active_date=today)  # filter by today's date

    for challenge in challenges:
        progress, created = UserChallengeProgress.objects.get_or_create(
            user=user,
            challenge=challenge,
            defaults={'progress': 0, 'completed': False}
        )

        # Reset progress if completed on previous day (daily reset)
        if progress.completed_at and progress.completed_at.date() < today:
            progress.completed = False
            progress.progress = 0

        if not progress.completed:
            if challenge.title == "Earn 30 points":
                progress.progress += points_earned
                if progress.progress >= challenge.target_value:
                    progress.completed = True
                    progress.completed_at = now()
                    user.profile.coins += challenge.reward_coins  # use challenge reward

            elif challenge.title == "Complete 3 lessons":
                if lesson_completed:
                    progress.progress += 1
                    if progress.progress >= challenge.target_value:
                        progress.completed = True
                        progress.completed_at = now()
                        user.profile.coins += challenge.reward_coins

            elif challenge.title == "Perfect accuracy":
                if accuracy == 100:
                    progress.completed = True
                    progress.completed_at = now()
                    user.profile.coins += challenge.reward_coins

            progress.save()
    user.profile.save()

@login_required
def redeem_challenge_reward(request, progress_id):
    try:
        progress = UserChallengeProgress.objects.get(id=progress_id, user=request.user)
        if progress.completed and not progress.rewarded:
            user_profile = request.user.profile
            user_profile.coins += progress.challenge.reward_coins
            user_profile.save()
            progress.rewarded = True
            progress.save()
            return JsonResponse({'success': True, 'new_coins': user_profile.coins})
        else:
            return JsonResponse({'success': False, 'message': 'Challenge not completed or already redeemed.'})
    except UserChallengeProgress.DoesNotExist:
        return HttpResponseBadRequest("Invalid challenge progress")
    