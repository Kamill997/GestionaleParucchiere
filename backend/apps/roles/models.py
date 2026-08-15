from django.db import models

from common.models import UUIDModel


class Permission(UUIDModel):
    """Permesso applicativo custom (distinto da django.contrib.auth.models.Permission).

    Schema PERMISSIONS in docs/02-backend.md: {uuid id PK, string chiave}.
    """

    chiave = models.CharField(
        max_length=150,
        unique=True,
        help_text='Identificativo del permesso, es. "prenotazioni.crea".',
    )

    class Meta:
        ordering = ['chiave']
        verbose_name = 'Permesso'
        verbose_name_plural = 'Permessi'

    def __str__(self) -> str:
        return self.chiave


class Role(UUIDModel):
    """Schema ROLES in docs/02-backend.md: {uuid id PK, string nome}.

    ROLE_PERMISSIONS e' la tabella ponte implicita creata dal ManyToManyField
    sottostante (nessun attributo extra richiesto sulla relazione).
    """

    nome = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, related_name='roles', blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Ruolo'
        verbose_name_plural = 'Ruoli'

    def __str__(self) -> str:
        return self.nome
