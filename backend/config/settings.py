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
        'user': '1000/hour',
        'anon': '100/hour',
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


# --- CORS ---
# Origini del frontend Vite (dev) + eventuali domini di produzione via env.
CORS_ALLOWED_ORIGINS = env.list('DJANGO_CORS_ALLOWED_ORIGINS', default=['http://localhost:5173'])
# Necessario per i cookie httpOnly dei token JWT (vedi docs/02-backend.md).
CORS_ALLOW_CREDENTIALS = True


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


# --- Celery ---
# Broker/backend condividono Redis con la cache (vedi docker-compose.yml, servizio celery-worker).

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
