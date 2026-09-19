"""
URL configuration — Sistema de Gestão Odontológica
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)

# ─── Admin ───────────────────────────────────────────────────────
admin.site.site_header = 'Sistema Odontológico — Admin'
admin.site.site_title  = 'Consultório Odontológico'
admin.site.index_title = 'Painel de Administração'

urlpatterns = [
    # Painel admin
    path('admin/', admin.site.urls),

    # API principal
    path('', include('principal.urls')),

    # Autenticação JWT
    path('api/token/',          TokenObtainPairView.as_view(),  name='token_obtain_pair'),
    path('api/token/refresh/',  TokenRefreshView.as_view(),     name='token_refresh'),
    path('api/token/verify/',   TokenVerifyView.as_view(),      name='token_verify'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(),  name='token_blacklist'),

    # Documentação OpenAPI
    path('api/schema/',  SpectacularAPIView.as_view(),                            name='schema'),
    path('api/docs/',    SpectacularSwaggerView.as_view(url_name='schema'),       name='swagger-ui'),
    path('api/redoc/',   SpectacularRedocView.as_view(url_name='schema'),         name='redoc'),
]

# ── Servir o frontend (HTML/CSS/JS/imagens) ──────────────────────
if settings.DEBUG:
    import os
    from django.views.static import serve as static_serve
    from django.http import FileResponse

    frontend_dir = settings.FRONTEND_DIR

    def serve_frontend(request, path='index.html'):
        """Serve os arquivos do frontend a partir da pasta /frontend/."""
        file_path = os.path.join(frontend_dir, path)
        if os.path.isfile(file_path):
            return FileResponse(open(file_path, 'rb'))
        # fallback para index.html (SPA)
        return FileResponse(open(os.path.join(frontend_dir, 'index.html'), 'rb'))

    urlpatterns += [
        path('',            serve_frontend,                   name='frontend-index'),
        path('<path:path>', serve_frontend,                   name='frontend-files'),
    ]

    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

