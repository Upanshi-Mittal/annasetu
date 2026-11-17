from django.urls import path

from donations import views

urlpatterns = [
    path('donations/', views.donation_list_view, name='donation_list'),
    path('donations/new/', views.donation_create_view, name='donation_create'),
    path('donations/<int:pk>/', views.donation_detail_view, name='donation_detail'),
    path('donations/<int:pk>/edit/', views.donation_edit_view, name='donation_edit'),
    path('donations/<int:pk>/cancel/', views.donation_cancel_view, name='donation_cancel'),
]
