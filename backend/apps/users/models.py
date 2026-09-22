import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class StatoUtente(models.TextChoices):
    ATTIVO = 'attivo', 'Attivo'
    INVITATO = 'invitato', 'Invitato'
    SOSPESO = 'sospeso', 'Sospeso'


class UserManager(BaseUserManager):
    """Manager custom: crea utenti per email invece che per username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Serve un indirizzo email.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Il superuser deve avere is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Il superuser deve avere is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Estende AbstractUser (vedi docs/02-backend.md, Autenticazione).

    first_name/last_name corrispondono a nome/cognome nello schema ER;
    date_joined corrisponde a created_at; password e' gia' l'hash.
    username resta presente per compatibilita' con AbstractUser ma non e'
    obbligatorio ne' usato per il login: si accede per email.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, blank=True, null=True, unique=False)
    email = models.EmailField('indirizzo email', unique=True)
    stato = models.CharField(max_length=20, choices=StatoUtente.choices, default=StatoUtente.ATTIVO)
    roles = models.ManyToManyField('roles.Role', related_name='users', blank=True)
    tokens_revoked_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ['email']
        verbose_name = 'Utente'
        verbose_name_plural = 'Utenti'

    def __str__(self):
        return self.email


def analizza_user_agent(ua_string: str) -> str:
    if not ua_string:
        return 'Dispositivo sconosciuto'
    ua = ua_string.lower()

    browser = 'Browser sconosciuto'
    if 'edg/' in ua:
        browser = 'Edge'
    elif 'chrome' in ua and 'safari' in ua and 'opr' not in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'opera' in ua or 'opr' in ua:
        browser = 'Opera'

    so = ''
    if 'windows' in ua:
        so = 'Windows'
    elif 'macintosh' in ua or 'mac os' in ua:
        so = 'macOS'
    elif 'iphone' in ua:
        so = 'iPhone'
    elif 'ipad' in ua:
        so = 'iPad'
    elif 'android' in ua:
        so = 'Android'
    elif 'linux' in ua:
        so = 'Linux'

    if browser and so:
        return f'{browser} su {so}'
    return browser or so or 'Dispositivo sconosciuto'


class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessioni')
    refresh_jti = models.CharField(max_length=255, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    dispositivo = models.CharField(max_length=150, blank=True)
    creato_il = models.DateTimeField(auto_now_add=True)
    ultimo_accesso = models.DateTimeField(auto_now=True)
    revocata = models.BooleanField(default=False)
    revocata_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-ultimo_accesso']
        verbose_name = 'Sessione utente'
        verbose_name_plural = 'Sessioni utente'

    def __str__(self):
        stato = 'revocata' if self.revocata else 'attiva'
        return f"Sessione {self.dispositivo or 'sconosciuto'} per {self.user.email} ({stato})"

