from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from common.permissions import read_only_or_roles_required

from .models import Disponibilita, Operatore
from .serializers import DisponibilitaSerializer, OperatoreSerializer


class OperatoreViewSet(viewsets.ModelViewSet):
    """Elenco operatori: lettura per chiunque sia autenticato (un Cliente
    deve poter scegliere l'operatore in fase di prenotazione), scrittura
    riservata all'Amministratore."""

    queryset = Operatore.objects.select_related('user').all()
    serializer_class = OperatoreSerializer
    permission_classes = [read_only_or_roles_required('Amministratore')]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['attivo']
    search_fields = ['nome', 'specializzazioni']


class DisponibilitaViewSet(viewsets.ModelViewSet):
    """Turni settimanali: lettura per tutti gli autenticati (serve al calcolo
    slot lato cliente), scrittura riservata all'Amministratore."""

    queryset = Disponibilita.objects.select_related('operatore').all()
    serializer_class = DisponibilitaSerializer
    permission_classes = [read_only_or_roles_required('Amministratore')]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['operatore', 'giorno_settimana']
