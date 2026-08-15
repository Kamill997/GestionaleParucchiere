"""Autenticazione JWT via cookie httpOnly.

docs/02-backend.md vieta di salvare i token in localStorage/sessionStorage
e richiede cookie httpOnly + Secure + SameSite. djangorestframework-simplejwt
di default legge il token dall'header Authorization: qui lo si legge invece
dal cookie impostato in apps/users/views.py.

Nota di sicurezza: DRF applica il controllo CSRF automaticamente solo per
SessionAuthentication. Con una authentication class custom basata su cookie,
il CSRF va rifatto esplicitamente qui sotto, altrimenti ogni richiesta che
sfrutta il cookie del browser sarebbe vulnerabile a CSRF.
"""

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            # Cookie scaduto/non valido: NON sollevare eccezione. Un access
            # token scaduto arriva automaticamente (e' un cookie) anche su
            # /api/v1/auth/refresh/ (AllowAny), che serve esattamente a
            # rinnovarlo: se qui si sollevasse un'eccezione, DRF risponderebbe
            # 401 prima ancora di eseguire la view di refresh.
            return None

        user = self.get_user(validated_token)
        self._enforce_csrf(request)
        return user, validated_token

    def _enforce_csrf(self, request):
        """Doppio-submit CSRF: il client deve inviare l'header X-CSRFToken
        con lo stesso valore del cookie csrftoken (impostato da
        GET /api/v1/auth/csrf/, vedi apps/users/views.py)."""
        check = CSRFCheck(lambda req: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f'Controllo CSRF fallito: {reason}')
