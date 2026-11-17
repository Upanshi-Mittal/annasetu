from django.urls import path

from logistics import views

urlpatterns = [
    path('logistics/claims/new/<int:donation_id>/', views.claim_create_view, name='claim_create'),
    path('logistics/claims/<int:claim_id>/accept/', views.claim_accept_view, name='claim_accept'),
    path('logistics/tasks/', views.task_list_view, name='task_list'),
    path('logistics/tasks/<int:pk>/', views.task_detail_view, name='task_detail'),
    path('logistics/tasks/<int:pk>/accept/', views.task_accept_view, name='task_accept'),
    path('logistics/tasks/<int:pk>/checklist/', views.task_safety_checklist_view, name='task_safety_checklist'),
    path('logistics/tasks/<int:pk>/scan/', views.task_scan_qr_view, name='task_scan_qr'),
]
