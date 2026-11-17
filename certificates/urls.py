from django.urls import path

from certificates import views

urlpatterns = [
    path('certificates/<int:pk>/download/', views.certificate_download_view, name='certificate_download'),
    path('certificates/donation/<int:donation_id>/', views.certificate_generate_donation_view, name='certificate_donation'),
    path('verify/<uuid:serial>/', views.certificate_verify_view, name='certificate_verify'),
]
