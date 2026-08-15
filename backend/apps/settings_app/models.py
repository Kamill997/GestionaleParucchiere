from django.db import models

from common.models import UUIDModel


class Impostazione(UUIDModel):
    """Configurazioni chiave/valore (docs/02-backend.md: "Settings - chiave/valore
    per configurazioni"). Niente multi-tenancy (vedi docs/02-backend.md,
    "Organization - presente solo se serve multi-tenancy": non e' il caso
    di questo progetto), quindi nessun organization_id: sono le impostazioni
    dell'unico salone gestito da questa istanza.
    """

    chiave = models.CharField(max_length=100, unique=True)
    valore = models.CharField(max_length=255)
    descrizione = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['chiave']
        verbose_name = 'Impostazione'
        verbose_name_plural = 'Impostazioni'

    def __str__(self):
        return f'{self.chiave} = {self.valore}'


# Chiavi note, con default: create pigramente (get_or_create) al primo
# accesso da get_int/get_str, cosi' l'app funziona anche prima che un
# amministratore le abbia configurate esplicitamente dal Django Admin.
DEFAULTS = {
    'buffer_minuti_prenotazioni': (
        '10',
        'Minuti di pulizia/preparazione tra due prenotazioni consecutive dello stesso operatore.',
    ),
    'intervallo_slot_minuti': (
        '15',
        "Granularita' orari di inizio proposti al cliente, indipendente dalla durata del servizio.",
    ),
    'ore_preavviso_cancellazione': (
        '24',
        'Ore minime di preavviso per una cancellazione libera da parte del cliente.',
    ),
    'soglia_no_show': (
        '3',
        'Numero di mancate presentazioni oltre il quale un cliente viene bloccato automaticamente.',
    ),
}


def get_int(chiave: str) -> int:
    default_valore, default_descrizione = DEFAULTS[chiave]
    impostazione, _ = Impostazione.objects.get_or_create(
        chiave=chiave, defaults={'valore': default_valore, 'descrizione': default_descrizione}
    )
    return int(impostazione.valore)
