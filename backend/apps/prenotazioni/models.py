from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models
from django.db.models import Func, Q

from apps.clienti.models import Cliente
from apps.operatori.models import Operatore
from apps.servizi.models import Servizio
from common.models import UUIDModel


class TsTzRange(Func):
    """Costruisce un tstzrange(inizio, fine) lato Postgres, usato solo
    dal vincolo di esclusione sotto (non e' un campo memorizzato)."""

    function = 'TSTZRANGE'
    output_field = DateTimeRangeField()


class StatoPrenotazione(models.TextChoices):
    CONFERMATA = 'confermata', 'Confermata'
    CANCELLATA = 'cancellata', 'Cancellata'
    COMPLETATA = 'completata', 'Completata'


class StatoPagamento(models.TextChoices):
    NON_PAGATO = 'non_pagato', 'Non pagato'
    PAGATO = 'pagato', 'Pagato'


class StatoPresenza(models.TextChoices):
    DA_VERIFICARE = 'da_verificare', 'Da verificare'
    PRESENTE = 'presente', 'Presente'
    NON_PRESENTE = 'non_presente', 'Non presente'


class Prenotazione(UUIDModel):
    """docs/esempio-settore-parrucchiere.md, entita' Prenotazioni - l'unica
    entita' realmente nuova rispetto allo scheletro generico.

    PROTECT sulle FK: cancellare uno Servizio/Operatore/Cliente con
    prenotazioni collegate non deve distruggere lo storico; per ritirare
    un servizio/operatore si usa il campo `attivo`, non la cancellazione.
    """

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='prenotazioni')
    operatore = models.ForeignKey(Operatore, on_delete=models.PROTECT, related_name='prenotazioni')
    servizio = models.ForeignKey(Servizio, on_delete=models.PROTECT, related_name='prenotazioni')
    inizio = models.DateTimeField()
    fine = models.DateTimeField()
    stato = models.CharField(
        max_length=20, choices=StatoPrenotazione.choices, default=StatoPrenotazione.CONFERMATA
    )
    # docs/08-pagamenti.md: dato amministrativo (il pagamento avviene fuori
    # dall'app), non una transazione elaborata dal sistema. `importo` parte
    # dal prezzo del servizio ma resta modificabile per sconti/eccezioni,
    # invece di richiedere una tabella pagamenti separata.
    stato_pagamento = models.CharField(
        max_length=20, choices=StatoPagamento.choices, default=StatoPagamento.NON_PAGATO
    )
    importo = models.DecimalField(max_digits=8, decimal_places=2)
    stato_presenza = models.CharField(
        max_length=20, choices=StatoPresenza.choices, default=StatoPresenza.DA_VERIFICARE
    )
    note = models.TextField(blank=True)
    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-inizio']
        verbose_name = 'Prenotazione'
        verbose_name_plural = 'Prenotazioni'
        constraints = [
            models.CheckConstraint(
                condition=Q(fine__gt=models.F('inizio')), name='prenotazioni_fine_dopo_inizio'
            ),
            # Prevenzione doppia prenotazione a livello di database (non solo
            # applicativo), richiesta esplicitamente da
            # docs/esempio-settore-parrucchiere.md per evitare race condition
            # con richieste simultanee. Il buffer tra prenotazioni (impostazione
            # configurabile) resta invece solo a livello applicativo, vedi
            # apps/prenotazioni/services.py.
            ExclusionConstraint(
                name='prenotazioni_no_overlap_operatore',
                expressions=[
                    ('operatore', RangeOperators.EQUAL),
                    (TsTzRange('inizio', 'fine'), RangeOperators.OVERLAPS),
                ],
                condition=~Q(stato=StatoPrenotazione.CANCELLATA),
            ),
        ]

    def __str__(self):
        return f'{self.cliente} con {self.operatore} - {self.inizio:%Y-%m-%d %H:%M}'

    def save(self, *args, **kwargs):
        # Default sensato invece di richiedere che ogni chiamante lo imposti
        # sempre esplicitamente (docs/08-pagamenti.md: "L'importo si ricava
        # dal prezzo del servizio associato... con possibilita' di
        # modificarlo manualmente"). Chi vuole uno sconto passa importo=
        # esplicitamente (vedi serializers.py, che lo fa solo alla creazione
        # se non gia' presente): qui si copre solo il caso "non specificato".
        if self.importo is None:
            self.importo = self.servizio.prezzo
        super().save(*args, **kwargs)
