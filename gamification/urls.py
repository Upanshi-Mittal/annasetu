from django.urls import path

from gamification import views

urlpatterns = [
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('tasks/<int:task_id>/rate/', views.rate_task_view, name='rate_task'),
]
