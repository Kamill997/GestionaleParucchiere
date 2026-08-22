from django.conf import settings
from django.db import models

from common.models import UUIDModel


class TipoNotifica(models.TextChoices):
    """docs/esempio-settore-parrucchiere.md ("Notifiche specifiche del
    settore") + docs/08-pagamenti.md ("Notifiche collegate")."""

    CONFERMA_PRENOTAZIONE = 'conferma_prenotazione', 'Conferma prenotazione'
    CANCELLAZIONE_PRENOTAZIONE = 'cancellazione_prenotazione', 'Cancellazione prenotazione'
    NUOVA_PRENOTAZIONE_RICEVUTA = 'nuova_prenotazione_ricevuta', 'Nuova prenotazione ricevuta'
    PROMEMORIA_PRENOTAZIONE = 'promemoria_prenotazione', 'Promemoria appuntamento'
    SOGLIA_NO_SHOW_RAGGIUNTA = 'soglia_no_show_raggiunta', 'Soglia no-show raggiunta'
    CLIENTE_BLOCCATO = 'cliente_bloccato', 'Cliente bloccato'
    CLIENTE_SBLOCCATO = 'cliente_sbloccato', 'Cliente sbloccato'


class Notifica(UUIDModel):
    """Notifiche in-app (docs/03-componenti-e-workflow.md: "In-app, email,
    push"). L'eventuale invio email avviene nello stesso momento in cui la
    notifica in-app viene creata (vedi services.crea_notifica), cosi' i due
    canali restano sempre coerenti tra loro invece di poter divergere.

    Un Cliente senza account (prenotazione da ospite, docs/08-pagamenti.md)
    non puo' avere una riga qui: destinatario e' sempre uno User. Per quel
    caso si invia solo l'email diretta all'indirizzo del Cliente, vedi
    services.notifica_cliente.
    """

    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifiche'
    )
    tipo = models.CharField(max_length=40, choices=TipoNotifica.choices)
    titolo = models.CharField(max_length=150)
    messaggio = models.TextField()
    link = models.CharField(
        max_length=255,
        blank=True,
        help_text="Percorso frontend relativo, es. '/le-mie-prenotazioni'.",
    )
    letta = models.BooleanField(default=False)
    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creato_il']
        verbose_name = 'Notifica'
        verbose_name_plural = 'Notifiche'

    def __str__(self):
        return f'{self.tipo} -> {self.destinatario} ({self.creato_il:%Y-%m-%d %H:%M})'
