"""Gestione centralizzata delle eccezioni per le API DRF.

Nato vuoto in Fase 1, popolato ora che serve davvero: eliminare un
Servizio/Operatore con Prenotazioni collegate (FK PROTECT, vedi
apps/prenotazioni/models.py) solleva django.db.models.ProtectedError, che
DRF non gestisce di default -> 500 invece di un errore chiaro all'utente.
"""

from django.db.models import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        return Response(
            {
                'detail': (
                    'Impossibile eliminare: ci sono altri record collegati '
                    '(es. prenotazioni). Disattivalo invece di eliminarlo.'
                )
            },
            status=400,
        )
    return drf_exception_handler(exc, context)
