from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import UUIDModel


class Operatore(UUIDModel):
    """Staff che eroga i servizi (docs/esempio-settore-parrucchiere.md).

    Estende `users.User` con un collegamento diretto (OneToOne) invece di
    duplicare i campi di autenticazione (vedi docs/02-backend.md). Il
    collegamento e' obbligatorio: un Operatore e' sempre anche un account
    con accesso al sistema (a differenza di Cliente, che puo' essere ospite).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='operatore'
    )
    nome = models.CharField(max_length=150)
    specializzazioni = models.CharField(max_length=255, blank=True)
    foto = models.ImageField(upload_to='operatori/', blank=True, null=True)
    attivo = models.BooleanField(
        default=True,
        help_text="Un operatore non attivo non e' selezionabile per nuove prenotazioni.",
    )

    class Meta:
        ordering = ['nome']
        verbose_name = 'Operatore'
        verbose_name_plural = 'Operatori'

    def __str__(self):
        return self.nome


class GiornoSettimana(models.IntegerChoices):
    """Stessa convenzione di date.weekday() in Python: 0=lunedi'...6=domenica,
    cosi' il calcolo disponibilita' non deve fare mappature aggiuntive."""

    LUNEDI = 0, 'Lunedì'
    MARTEDI = 1, 'Martedì'
    MERCOLEDI = 2, 'Mercoledì'
    GIOVEDI = 3, 'Giovedì'
    VENERDI = 4, 'Venerdì'
    SABATO = 5, 'Sabato'
    DOMENICA = 6, 'Domenica'


class Disponibilita(UUIDModel):
    """Turno settimanale standard di un operatore (docs/esempio-settore-parrucchiere.md,
    entita' "Disponibilita' operatore"). Le eccezioni puntuali (ferie,
    permessi, chiusure straordinarie) non sono ancora modellate: restano
    un'estensione futura esplicitamente citata nei docs ma non ancora
    nello schema ER di base.
    """

    operatore = models.ForeignKey(Operatore, on_delete=models.CASCADE, related_name='disponibilita')
    giorno_settimana = models.IntegerField(choices=GiornoSettimana.choices)
    ora_inizio = models.TimeField()
    ora_fine = models.TimeField()

    class Meta:
        ordering = ['giorno_settimana', 'ora_inizio']
        verbose_name = 'Disponibilità'
        verbose_name_plural = 'Disponibilità'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ora_fine__gt=models.F('ora_inizio')),
                name='disponibilita_ora_fine_dopo_ora_inizio',
            )
        ]

    def __str__(self):
        giorno = self.get_giorno_settimana_display()
        return f'{self.operatore} - {giorno} {self.ora_inizio}-{self.ora_fine}'


class TipoEccezione(models.TextChoices):
    FERIE = 'ferie', 'Ferie'
    MALATTIA = 'malattia', 'Malattia'
    PERMESSO = 'permesso', 'Permesso'
    CHIUSURA = 'chiusura', 'Chiusura salone'


class EccezioneDisponibilita(UUIDModel):
    """Eccezioni alla disponibilità ordinaria:
    - Se operatore è valorizzato: assenza/ferie/permesso di quel collaboratore.
    - Se operatore è null: chiusura straordinaria dell'intero salone (festività, ferie aziendali, ecc.).
    - Se ora_inizio e ora_fine sono null: copre l'intera giornata/periodo.
    - Se ora_inizio e ora_fine sono valorizzati: copre solo quella fascia oraria specifica.
    """

    operatore = models.ForeignKey(
        Operatore,
        on_delete=models.CASCADE,
        related_name='eccezioni',
        null=True,
        blank=True,
        help_text="Lasciare vuoto se si tratta di una chiusura dell'intero salone.",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoEccezione.choices,
        default=TipoEccezione.FERIE,
    )
    data_inizio = models.DateField()
    data_fine = models.DateField()
    ora_inizio = models.TimeField(null=True, blank=True)
    ora_fine = models.TimeField(null=True, blank=True)
    motivo = models.CharField(max_length=255, blank=True)
    creato_il = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-data_inizio', 'ora_inizio']
        verbose_name = 'Eccezione disponibilità'
        verbose_name_plural = 'Eccezioni disponibilità'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(data_fine__gte=models.F('data_inizio')),
                name='eccezione_data_fine_dopo_data_inizio',
            ),
        ]

    def __str__(self):
        soggetto = self.operatore.nome if self.operatore else 'Salone'
        return f'{soggetto} - {self.get_tipo_display()} ({self.data_inizio} -> {self.data_fine})'

