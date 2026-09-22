from rest_framework.settings import api_settings
from rest_framework.throttling import AnonRateThrottle


class BaseIpRateThrottle(AnonRateThrottle):
    """Estrae l'indirizzo IP del client reale gestendo header di proxy (es. Traefik, Railway, Nginx)."""

    def get_ident(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class LoginRateThrottle(BaseIpRateThrottle):
    """Rate limit mirato per IP sull'endpoint di autenticazione (/api/v1/auth/login/).

    Protegge da attacchi brute-force e credential stuffing.
    La frequenza massima consentita e' configurabile tramite la chiave 'login'
    in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] (es. '5/min' in produzione).
    """

    scope = 'login'

    def get_rate(self):
        return api_settings.DEFAULT_THROTTLE_RATES.get(self.scope, '5/min')


class PasswordResetRateThrottle(BaseIpRateThrottle):
    """Rate limit mirato per IP sull'endpoint di richiesta reset password.

    Previene attacchi di email bombing ed enumerazione massiva.
    """

    scope = 'password_reset'

    def get_rate(self):
        return api_settings.DEFAULT_THROTTLE_RATES.get(self.scope, '3/min')


class RegisterRateThrottle(BaseIpRateThrottle):
    """Rate limit mirato per IP sull'endpoint di auto-registrazione.

    Previene la creazione automatizzata di account fittizi o bot.
    """

    scope = 'register'

    def get_rate(self):
        return api_settings.DEFAULT_THROTTLE_RATES.get(self.scope, '10/hour')


