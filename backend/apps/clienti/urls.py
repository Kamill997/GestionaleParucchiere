from rest_framework.routers import DefaultRouter

from .views import ClienteViewSet

router = DefaultRouter()
router.register('clienti', ClienteViewSet, basename='clienti')

urlpatterns = router.urls
