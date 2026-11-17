"""AnnaSetu — Root URL configuration."""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),

    # API
    path("api/v1/", include("api.urls")),

    # Debug toolbar
    *([path("__debug__/", include("debug_toolbar.urls"))] if settings.DEBUG else []),
]

# i18n-prefixed patterns
urlpatterns += i18n_patterns(
    path("", include("accounts.urls")),
    path("", include("donations.urls")),
    path("", include("logistics.urls")),
    path("", include("notifications.urls")),
    path("", include("analytics.urls")),
    path("", include("gamification.urls")),
    path("", include("moderation.urls")),
    path("", include("certificates.urls")),
    prefix_default_language=False,
)

# Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = "accounts.views.handler404"
handler500 = "accounts.views.handler500"
