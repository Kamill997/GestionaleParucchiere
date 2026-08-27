"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from health_check.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Fase 9 — Monitoraggio: verifica DB, cache e storage. Usato dagli
    # healthcheck di Docker (vedi docker-compose.yml) e dai provider di
    # hosting (Railway/Render). Non richiede autenticazione: restituisce
    # solo "OK" o un elenco di servizi degradati, nessun dato sensibile.
    # django-health-check v4+ non ha piu' un modulo urls separato:
    # si monta direttamente la view.
    path('health/', HealthCheckView.as_view(), name='health'),
    # Documentazione API automatica (vedi docs/02-backend.md, "Design delle API")
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # Rotte applicative, un modulo alla volta a partire da Fase 2.
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.servizi.urls')),
    path('api/v1/', include('apps.operatori.urls')),
    path('api/v1/', include('apps.clienti.urls')),
    path('api/v1/', include('apps.prenotazioni.urls')),
    path('api/v1/', include('apps.notifiche.urls')),
    path('api/v1/', include('apps.settings_app.urls')),
]

if settings.DEBUG:
    # Solo per sviluppo: in produzione i file media li serve lo storage
    # S3 (django-storages) o il reverse proxy, non Django (vedi docs/02-backend.md).
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
