from rest_framework.routers import DefaultRouter

from .views import DisponibilitaViewSet, OperatoreViewSet

router = DefaultRouter()
router.register('operatori', OperatoreViewSet, basename='operatori')
router.register('disponibilita', DisponibilitaViewSet, basename='disponibilita')

urlpatterns = router.urls
