from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.urls import path, register_converter
import uuid
from .views import challenges_view

class UUIDConverter:
    regex = '[0-9a-f-]{36}'

    def to_python(self, value):
        return uuid.UUID(value)

    def to_url(self, value):
        return str(value)

register_converter(UUIDConverter, 'uuid')

urlpatterns = [
    #authorisation
    path('login/', views.custom_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register, name='register'),

    #pages
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('training/', views.training, name='training'),
    path('shop/', views.shop, name='shop'),
    path('profile/', views.profile, name='profile'),

    #lessons
    path('lesson/<uuid:lesson_id>/page/<int:page>/', views.lesson_page, name='lesson_page'),
    path('lesson/<uuid:lesson_id>/result/', views.lesson_result, name='lesson_result'),
    path('lesson/<uuid:lesson_id>/end/', views.end_lesson, name='end_lesson'),
    path('ajax/check-answer/', views.check_answer, name='ajax_check_answer'),

    #leaderboard
    path('leaderboard/', views.leaderboard, name='leaderboard'),

    #Challenges
    path('challenges/', challenges_view, name='challenges'),
    path('challenges/redeem/<int:progress_id>/', views.redeem_challenge_reward, name='redeem_challenge_reward'),
]
