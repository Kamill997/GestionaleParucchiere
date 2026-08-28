from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NotificaViewSet, PushSubscribeView, VapidPublicKeyView

router = DefaultRouter()
router.register('notifiche', NotificaViewSet, basename='notifiche')

urlpatterns = [
    path('notifiche/push-subscribe/', PushSubscribeView.as_view(), name='push-subscribe'),
    path('notifiche/vapid-public-key/', VapidPublicKeyView.as_view(), name='vapid-public-key'),
    *router.urls,
]
