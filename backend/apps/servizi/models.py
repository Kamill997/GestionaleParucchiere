from django.core.validators import MinValueValidator
from django.db import models

from common.models import UUIDModel


class Servizio(UUIDModel):
    """Listino servizi del salone (docs/esempio-settore-parrucchiere.md,
    "Entita' di dominio"): nome, descrizione, categoria, durata, prezzo, foto.

    `categoria` resta testo libero (non un enum fisso): saloni diversi
    possono avere categorie diverse, non e' un valore su cui vale la pena
    irrigidire lo schema.
    """

    nome = models.CharField(max_length=150)
    descrizione = models.TextField(blank=True)
    categoria = models.CharField(
        max_length=50,
        help_text='Es. "Taglio", "Colore", "Trattamento", "Barba".',
    )
    durata_minuti = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    prezzo = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    foto = models.ImageField(upload_to='servizi/', blank=True, null=True)
    attivo = models.BooleanField(
        default=True, help_text="Un servizio disattivato non compare piu' nel catalogo cliente."
    )

    class Meta:
        ordering = ['categoria', 'nome']
        verbose_name = 'Servizio'
        verbose_name_plural = 'Servizi'

    def __str__(self):
        return f'{self.nome} ({self.categoria})'
