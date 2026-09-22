"""Middleware di sicurezza HTTP per aggiungere header di protezione moderni,
inclusa una Content Security Policy (CSP) conforme agli standard OWASP.
"""

from django.conf import settings

CSP_DIRECTIVES = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
    "font-src 'self' https://fonts.gstatic.com data:",
    "img-src 'self' data: blob: http://localhost:8000 https://cdn.jsdelivr.net",
    "connect-src 'self' http://localhost:8000 http://localhost:5173 ws://localhost:5173",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
]

CSP_HEADER_VALUE = '; '.join(CSP_DIRECTIVES)


class ContentSecurityPolicyMiddleware:
    """Aggiunge l'header Content-Security-Policy e altri header di protezione essenziali."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Imposta Content-Security-Policy se non gia' presente
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = CSP_HEADER_VALUE

        # Header aggiuntivi di hardening HTTP
        if 'X-Content-Type-Options' not in response:
            response['X-Content-Type-Options'] = 'nosniff'

        if 'Referrer-Policy' not in response:
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        return response
