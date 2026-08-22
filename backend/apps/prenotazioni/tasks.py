"""Task Celery per le prenotazioni (docs/esempio-settore-parrucchiere.md,
"Notifiche specifiche del settore": "Promemoria (es. 24h prima) -> Cliente").

La schedulazione periodica (Celery Beat, es. ogni 15 minuti) e' un passo di
configurazione/deployment non esercitato in questo ambiente sandbox (nessun
worker/scheduler persistente disponibile qui): la logica del task e' scritta
e testata chiamandola direttamente, la schedulazione resta da collegare in
produzione (vedi docker-compose.yml per il servizio celery-worker gia'
presente; manca ancora un servizio/comando celery beat dedicato).
"""

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.notifiche.models import TipoNotifica
from apps.notifiche.services import notifica_cliente

from .models import Prenotazione, StatoPrenotazione


@shared_task
def invia_promemoria_prenotazioni(ore_anticipo=24, finestra_minuti=15):
    """Trova le prenotazioni confermate che iniziano tra `ore_anticipo` ore
    e `ore_anticipo` ore + `finestra_minuti` da adesso, e invia un
    promemoria. Pensato per girare periodicamente con un intervallo pari a
    `finestra_minuti`: ogni prenotazione attraversa la finestra una sola
    volta, quindi riceve un solo promemoria senza bisogno di un flag
    "gia' inviato" separato - a patto che il task giri davvero con quella
    cadenza (vedi nota sulla schedulazione in cima al file).
    """
    adesso = timezone.now()
    inizio_finestra = adesso + timedelta(hours=ore_anticipo)
    fine_finestra = inizio_finestra + timedelta(minutes=finestra_minuti)

    prenotazioni = Prenotazione.objects.filter(
        stato=StatoPrenotazione.CONFERMATA,
        inizio__gte=inizio_finestra,
        inizio__lt=fine_finestra,
    ).select_related('cliente', 'servizio')

    inviati = 0
    for prenotazione in prenotazioni:
        notifica_cliente(
            prenotazione.cliente,
            TipoNotifica.PROMEMORIA_PRENOTAZIONE,
            'Promemoria appuntamento',
            f'Ti aspettiamo alle {prenotazione.inizio:%H:%M} del '
            f'{prenotazione.inizio:%d/%m} per {prenotazione.servizio.nome}.',
            link='/le-mie-prenotazioni',
        )
        inviati += 1
    return inviati
