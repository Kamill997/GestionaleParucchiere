from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ChangePasswordView,
    CsrfCookieView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshView,
    RegisterView,
    UserAdminViewSet,
    UserSessionViewSet,
)

router = DefaultRouter()
router.register('admin/utenti', UserAdminViewSet, basename='admin-utenti')
router.register('auth/sessioni', UserSessionViewSet, basename='auth-sessioni')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('auth/csrf/', CsrfCookieView.as_view(), name='auth-csrf'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path(
        'auth/password-reset-confirm/',
        PasswordResetConfirmView.as_view(),
        name='auth-password-reset-confirm',
    ),
    path('', include(router.urls)),
]
