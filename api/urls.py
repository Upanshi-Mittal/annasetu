from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import (
    ClaimViewSet,
    DeliveryTaskViewSet,
    DonationViewSet,
    NotificationViewSet,
    QRScanViewSet,
    UserProfileViewSet,
)

router = DefaultRouter()
router.register(r'users', UserProfileViewSet, basename='user')
router.register(r'donations', DonationViewSet, basename='donation')
router.register(r'claims', ClaimViewSet, basename='claim')
router.register(r'tasks', DeliveryTaskViewSet, basename='task')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'qr', QRScanViewSet, basename='qr')

urlpatterns = [
    # JWT Auth
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Schema & Docs
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Routers
    path('', include(router.urls)),
]
