"""
Django settings per il progetto "config".

Fase 1 (Setup): ambiente (env vars, DB, cache, JWT, CORS, API schema) come
descritto in docs/02-backend.md e docs/06-docker-e-cicd.md.

Fase 2 (in corso - autenticazione e ruoli, docs/10-guida-vibe-coding.md):
AUTH_USER_MODEL impostato su apps.users.User PRIMA di qualunque migrate
reale (vedi apps/users/models.py). Autenticazione via JWT in cookie
httpOnly (non Authorization header): docs/02-backend.md vieta di salvare
i token in localStorage/sessionStorage. Questo richiede una authentication
class custom (common/authentication.py) e protezione CSRF esplicita,
perche' DRF applica il controllo CSRF automaticamente solo con
SessionAuthentication, non con classi custom.
"""

import sys
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# .env vive nella root del repo (accanto a docker-compose.yml), non in backend/,
# cosi' resta un solo .env.example condiviso (vedi docs/06-docker-e-cicd.md).
# In produzione le env vars arrivano dal provider di hosting, non da questo file.
environ.Env.read_env(BASE_DIR.parent / '.env')

# --- Core ---

SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-dev-only-do-not-use-in-production')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[])

AUTH_USER_MODEL = 'users.User'

# --- Sicurezza (Fase 6) ---
# Attivi solo in produzione (DEBUG=False) per non rompere lo sviluppo locale
# che gira su http, senza HTTPS. Coerenti con docs/04-pwa-checklist.md che
# richede HTTPS obbligatorio e con docs/09-hosting-e-dominio.md.
if not DEBUG:
    SECURE_HSTS_SECONDS = 31_536_000  # 1 anno
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    # --- Sentry (Fase 9 — Monitoraggio) ---
    # Inizializzato solo in produzione, mai in sviluppo o nei test
    # (riduplicherebbe errori intenzionali dei test come rumore nel tracker).
    # SENTRY_DSN viene dalla variabile d'ambiente, mai committato nel repo.
    _sentry_dsn = env('SENTRY_DSN', default='')
    if _sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[DjangoIntegration(), CeleryIntegration()],
            # Campiona il 10% delle transazioni per le performance
            # (aggiustare dopo aver visto i volumi reali in produzione).
            traces_sample_rate=0.1,
            # Non inviare PII (email utente, IP) a Sentry di default:
            # rispetta il GDPR senza configurazione aggiuntiva.
            send_default_pii=False,
        )


# --- Application definition ---

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terze parti
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'corsheaders',
    'drf_spectacular',
    # App di progetto (vedi docs/02-backend.md, struttura cartelle)
    'apps.users',
    'apps.roles',
    'apps.servizi',
    'apps.operatori',
    'apps.clienti',
    'apps.prenotazioni',
    'apps.notifiche',
    'apps.audit_log',
    'apps.settings_app',
    # Fase 9 — Monitoraggio: endpoint /health per Docker healthcheck e
    # provider di hosting (vedi docs/06-docker-e-cicd.md). La versione v4+
    # di django-health-check non separa piu' i check in sottomoduli distinti:
    # il check di DB, cache e storage e' incluso nel pacchetto base.
    'health_check',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # va prima di CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.middleware.ContentSecurityPolicyMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- Database ---
# DATABASE_URL impostata da docker-compose.yml (Postgres). Fallback a sqlite
# solo per poter eseguire comandi di management senza Docker in locale.
DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
}


# --- Password validation ---

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internazionalizzazione ---
# Progetto per il mercato italiano (vedi esempio-settore-parrucchiere.md)

LANGUAGE_CODE = 'it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_TZ = True


# --- Static / media files ---

# STATIC_ROOT richiesto da `collectstatic` nello stage production del Dockerfile.
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Locale per ora; passa a S3 (django-storages) quando servono upload reali.
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Django REST Framework ---

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('common.authentication.CookieJWTAuthentication',),
    'EXCEPTION_HANDLER': 'common.exceptions.exception_handler',
    # Secure-by-default: gli endpoint pubblici (login, registrazione) fatti
    # in Fase 2 dovranno sovrascrivere esplicitamente con AllowAny.
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardResultsSetPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'user': env('THROTTLE_USER_RATE', default='10000/hour' if DEBUG else '1000/hour'),
        'anon': env('THROTTLE_ANON_RATE', default='10000/hour' if DEBUG else '100/hour'),
        'login': env('THROTTLE_LOGIN_RATE', default='10000/hour' if DEBUG else '5/min'),
        'password_reset': env('THROTTLE_PASSWORD_RESET_RATE', default='10000/hour' if DEBUG else '3/min'),
        'register': env('THROTTLE_REGISTER_RATE', default='10000/hour' if DEBUG else '10/hour'),
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Gestionale API',
    'DESCRIPTION': 'API del gestionale (vedi docs/00-README.md per il contesto del progetto).',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# --- JWT (djangorestframework-simplejwt) ---

_jwt_access_minutes = env.int('JWT_ACCESS_EXPIRATION_MINUTES', default=15)
_jwt_refresh_days = env.int('JWT_REFRESH_EXPIRATION_DAYS', default=30)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=_jwt_access_minutes),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=_jwt_refresh_days),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Cookie httpOnly per i token JWT (mai localStorage/sessionStorage,
# vedi docs/02-backend.md "Autenticazione"). Letti/scritti in apps/users/views.py
# e common/authentication.py.
AUTH_COOKIE_ACCESS = 'access_token'
AUTH_COOKIE_REFRESH = 'refresh_token'
AUTH_COOKIE_REFRESH_PATH = '/api/v1/auth/'
AUTH_COOKIE_SECURE = (
    not DEBUG
)  # True in produzione: richiede HTTPS (coerente con docs/09-hosting-e-dominio.md)
AUTH_COOKIE_SAMESITE = 'Lax'


# --- CORS & CSRF ---
# Origini del frontend Vite (dev) + eventuali domini di produzione via env.
CORS_ALLOWED_ORIGINS = env.list(
    'DJANGO_CORS_ALLOWED_ORIGINS',
    default=['http://localhost:5173', 'http://127.0.0.1:5173'],
)
# Necessario per i cookie httpOnly dei token JWT (vedi docs/02-backend.md).
CORS_ALLOW_CREDENTIALS = True

# Origini fidate per il controllo CSRF (Django 4+ confronta l'header HTTP Origin)
CSRF_TRUSTED_ORIGINS = env.list(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    default=[
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ],
)


# --- Cache (Redis) ---

REDIS_URL = env('REDIS_URL', default='redis://localhost:6379')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}

if 'pytest' in sys.modules:
    # I test devono restare isolati/ripetibili: con Redis reale, i contatori
    # di throttling DRF (vedi DEFAULT_THROTTLE_RATES sopra) si accumulano
    # tra una run di pytest e l'altra fino a restituire 429 "Too Many
    # Requests" anche su richieste legittime - bug reale osservato in
    # sviluppo. La CI (.github/workflows/ci.yml) inoltre non avvia un
    # servizio Redis per i test: anche per quello serve una cache locale.
    CACHES['default'] = {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}

    # Anche con LocMemCache non basta: con una suite abbastanza grande
    # (79 test, ognuno con piu' richieste anonime a /auth/login//csrf/) si
    # supera comunque "100/hour" dentro un solo processo di test - bug
    # reale osservato appena la suite e' cresciuta. Il throttling e' un
    # comportamento da verificare con test dedicati e isolati (con una
    # rate impostata apposta), non un'interferenza di sottofondo su tutta
    # la suite.
    REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []


# --- Email (apps.notifiche) ---
# In sviluppo il default è console.EmailBackend (stampa nei log). In produzione o configurando
# le variabili SMTP in .env (es. Gmail, Brevo, SendGrid), invia vere email ai destinatari.
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='no-reply@gestionale-salone.local')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_TIMEOUT = env.int('EMAIL_TIMEOUT', default=10)


# --- VAPID (notifiche push PWA, docs/04-pwa-checklist.md) ---
VAPID_PRIVATE_KEY = env('VAPID_PRIVATE_KEY', default='')
VAPID_PUBLIC_KEY = env('VAPID_PUBLIC_KEY', default='')
VAPID_ADMIN_EMAIL = env('VAPID_ADMIN_EMAIL', default='admin@gestionale.local')

# --- Logging (Fase 9) ---
# Checklist pre-lancio: "verifica che i dati sensibili non compaiano nei log".
# In sviluppo: console leggibile. In produzione: JSON su stdout (catturato
# da Railway/Cloudflare), livello WARNING per ridurre il rumore. I campi
# sensibili (password, token, VAPID_PRIVATE_KEY) non vengono mai loggati
# perche': 1) non li passiamo mai a logger.* nel codice (verificato), 2)
# Django oscura automaticamente i valori di SENSITIVE_VARIABLES nei
# traceback dei form/request (vedi sotto).
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING' if not DEBUG else 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING' if not DEBUG else 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Oscura automaticamente i valori di questi campi nel pannello debug di Django
# (request POST, sessioni). Non serve in produzione (DEBUG=False li nasconde
# tutti), ma e' buona pratica averlo anche in sviluppo.
SENSITIVE_VARIABLES = ('password', 'token', 'access_token', 'refresh_token', 'vapid_private_key')
SENSITIVE_POST_PARAMETERS = ('password', 'password1', 'password2')

# --- Celery ---
# Broker/backend condividono Redis con la cache (vedi docker-compose.yml, servizio celery-worker).

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# --- Celery Beat (schedulazione task periodici) ---
# Il servizio celery-beat nel docker-compose.yml legge questa configurazione
# e lancia i task alla cadenza indicata. Ogni task va programmato alla stessa
# cadenza di `finestra_minuti` (default 15) usata in
# apps/prenotazioni/tasks.invia_promemoria_prenotazioni: in questo modo ogni
# prenotazione attraversa la finestra una sola volta ricevendo un solo
# promemoria, senza bisogno di un flag "gia' inviato" separato (vedi commento
# nella funzione stessa).

from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    'promemoria-prenotazioni-ogni-15-minuti': {
        'task': 'apps.prenotazioni.tasks.invia_promemoria_prenotazioni',
        'schedule': crontab(minute='*/15'),
        'kwargs': {'ore_anticipo': 24, 'finestra_minuti': 15},
    },
}
