from django.urls import path

from moderation import views

urlpatterns = [
    path('report/', views.report_create_view, name='report_create'),
]
