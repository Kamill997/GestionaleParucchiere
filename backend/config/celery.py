import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Legge la configurazione Celery da settings.py, prefisso CELERY_*
# (es. CELERY_BROKER_URL), invece di duplicarla qui.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autoregistra un modulo tasks.py per ogni app in INSTALLED_APPS.
app.autodiscover_tasks()
