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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ['email']
        verbose_name = 'Utente'
        verbose_name_plural = 'Utenti'

    def __str__(self):
        return self.email
