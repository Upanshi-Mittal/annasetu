from django.urls import path

from analytics import views

urlpatterns = [
    path('impact/', views.impact_page_view, name='impact'),
    path('api/heatmap-data/', views.heatmap_data_api, name='heatmap_data'),
]
