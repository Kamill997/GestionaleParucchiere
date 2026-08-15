from django.conf import settings
from django.db import models

from common.models import UUIDModel


class Cliente(UUIDModel):
    """Anagrafica clienti (docs/esempio-settore-parrucchiere.md).

    `user` e' NULLABLE: a differenza di Operatore, un Cliente puo' esistere
    senza un account (prenotazione da ospite), come descritto esplicitamente
    in docs/08-pagamenti.md per il conteggio no-show via email/telefono.
    `email`/`telefono` restano quindi campi propri del Cliente, non solo
    ereditati dallo User collegato.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cliente',
    )
    nome = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    note_preferenze = models.TextField(
        blank=True,
        help_text='Es. colore abituale. Se contiene dati sanitari (es. allergie), '
        'trattare come categoria particolare di dati ai sensi del GDPR '
        '(vedi docs/esempio-settore-parrucchiere.md, sezione "Nota").',
    )
    # docs/08-pagamenti.md, "Politica no-show". Gestiti solo tramite
    # apps/prenotazioni/services.py (incremento automatico) e l'azione
    # 'sblocca' (vedi apps/clienti/views.py): mai scrivibili via API diretta,
    # sono stato derivato dallo storico presenze, non un dato libero.
    contatore_no_show = models.PositiveIntegerField(default=0)
    bloccato = models.BooleanField(
        default=False,
        help_text='Blocca nuove prenotazioni da questo cliente (soglia no-show raggiunta).',
    )

    class Meta:
        ordering = ['nome']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clienti'

    def __str__(self):
        return self.nome
