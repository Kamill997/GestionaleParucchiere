from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CsrfCookieView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    RegisterView,
    UserAdminViewSet,
)

router = DefaultRouter()
router.register('admin/utenti', UserAdminViewSet, basename='admin-utenti')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('auth/csrf/', CsrfCookieView.as_view(), name='auth-csrf'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('', include(router.urls)),
]
