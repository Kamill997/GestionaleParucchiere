"""Notifiche push via Web Push + VAPID (docs/04-pwa-checklist.md,
"Notifiche push": "Push API + Notification API lato client, chiavi VAPID
lato backend, pywebpush"). Tenuto separato da services.py per non
importare pywebpush in ambienti dove le chiavi VAPID non sono configurate
(sviluppo locale, CI) - services.py continua a funzionare normalmente
anche senza queste variabili d'ambiente.

Uso:
  from apps.notifiche.push_services import invia_push_a_utente
  invia_push_a_utente(user, titolo='...', corpo='...', link='/rotta')
"""

import json
import logging
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from apps.users.models import User

logger = logging.getLogger(__name__)


def _leggi_chiavi_vapid() -> tuple[str, str] | None:
    """Restituisce (private_key, public_key) o None se non configurate."""
    priv = getattr(settings, 'VAPID_PRIVATE_KEY', '')
    pub = getattr(settings, 'VAPID_PUBLIC_KEY', '')
    if not priv or not pub:
        return None
    return priv, pub


def invia_push_a_sottoscrizione(sottoscrizione: dict, titolo: str, corpo: str, link='') -> bool:
    """Invia una notifica push a una singola sottoscrizione.

    `sottoscrizione`: il dict deserializzato di PushSubscription (endpoint,
    keys.auth, keys.p256dh) salvato dal browser al momento del consenso
    (vedi frontend/src/features/notifiche/push.ts).

    Restituisce True se l'invio e' riuscito, False altrimenti (la riga
    di sottoscrizione va eliminata se il server risponde con 410 Gone,
    ovvero il browser ha revocato il permesso - vedi invio_push_a_utente).
    """
    chiavi = _leggi_chiavi_vapid()
    if chiavi is None:
        logger.debug('VAPID non configurato, invio push saltato.')
        return False

    try:
        from pywebpush import webpush

        webpush(
            subscription_info=sottoscrizione,
            data=json.dumps({'title': titolo, 'body': corpo, 'url': link}),
            vapid_private_key=chiavi[0],
            vapid_claims={
                'sub': f'mailto:{getattr(settings, "VAPID_ADMIN_EMAIL", "admin@gestionale.local")}'
            },
        )
        return True
    except Exception as exc:
        if hasattr(exc, 'response') and getattr(exc.response, 'status_code', 0) == 410:
            # 410 Gone: il browser ha revocato il permesso, la sottoscrizione
            # non esiste piu' - va eliminata (lo fa il chiamante).
            return False
        logger.warning('Invio push fallito: %s', exc)
        return False


def invia_push_a_utente(user: 'User', titolo: str, corpo: str, link='') -> int:
    """Invia a tutte le sottoscrizioni attive di un utente e rimuove
    quelle scadute (410 Gone). Restituisce il numero di push riusciti."""
    from .models import PushSubscription

    sottoscrizioni = PushSubscription.objects.filter(utente=user)
    riusciti = 0
    scadute = []

    for sub in sottoscrizioni:
        ok = invia_push_a_sottoscrizione(sub.subscription_data, titolo, corpo, link)
        if ok:
            riusciti += 1
        else:
            scadute.append(sub.id)

    if scadute:
        PushSubscription.objects.filter(id__in=scadute).delete()

    return riusciti
