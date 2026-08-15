from django.conf import settings
from django.db import models

from common.models import UUIDModel


class AuditLog(UUIDModel):
    """Schema AUDIT_LOG in docs/02-backend.md: id, user, azione, entita
    coinvolta, timestamp, dettagli (JSONField, nativo con Postgres).

    on_delete=SET_NULL: la voce di audit deve sopravvivere anche se l'utente
    che ha compiuto l'azione viene in seguito eliminato (integrita' dello
    storico ai fini di audit/compliance).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_log_entries',
    )
    azione = models.CharField(max_length=100)
    entita_coinvolta = models.CharField(max_length=100)
    dettagli = models.JSONField(default=dict, blank=True)
    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creato_il']
        verbose_name = 'Voce di audit'
        verbose_name_plural = 'Log di audit'

    def __str__(self):
        return f'{self.azione} su {self.entita_coinvolta} ({self.creato_il:%Y-%m-%d %H:%M})'
