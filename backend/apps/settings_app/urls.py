from rest_framework.routers import DefaultRouter

from .views import ImpostazioneViewSet

router = DefaultRouter()
router.register('impostazioni', ImpostazioneViewSet, basename='impostazioni')

urlpatterns = router.urls
