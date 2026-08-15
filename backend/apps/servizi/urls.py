from rest_framework.routers import DefaultRouter

from .views import ServizioViewSet

router = DefaultRouter()
router.register('servizi', ServizioViewSet, basename='servizi')

urlpatterns = router.urls
