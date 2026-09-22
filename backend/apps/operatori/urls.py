from rest_framework.routers import DefaultRouter

from .views import DisponibilitaViewSet, EccezioneDisponibilitaViewSet, OperatoreViewSet

router = DefaultRouter()
router.register('operatori', OperatoreViewSet, basename='operatori')
router.register('disponibilita', DisponibilitaViewSet, basename='disponibilita')
router.register(
    'eccezioni-disponibilita',
    EccezioneDisponibilitaViewSet,
    basename='eccezioni-disponibilita',
)

urlpatterns = router.urls
