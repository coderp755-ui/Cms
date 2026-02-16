from django.conf import settings
from django.urls import include, path
from urls.Accounts_urls import urlpatterns as Accounts_urls
from urls.Classes_urls import urlpatterns as Classes_urls
from urls.Tests_urls import urlpatterns as Tests_urls
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenRefreshView
from apps.acounts.backends import CustomTokenObtainPairView


urlpatterns = [
    # path('admin/', admin.site.urls),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(Accounts_urls)),
    path("", include(Classes_urls)),
    path("", include(Tests_urls)),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
        # API Documentation (only in development)
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/swagger/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/docs/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ] + urlpatterns

    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
