from rest_framework.routers import DefaultRouter

from .views import NotificaViewSet

router = DefaultRouter()
router.register('notifiche', NotificaViewSet, basename='notifiche')

urlpatterns = router.urls
