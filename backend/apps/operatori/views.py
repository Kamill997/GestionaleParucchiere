from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from common.permissions import read_only_or_roles_required

from .models import Disponibilita, EccezioneDisponibilita, Operatore
from .serializers import (
    DisponibilitaSerializer,
    EccezioneDisponibilitaSerializer,
    OperatoreSerializer,
)


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
    slot lato cliente), scrittura per Amministratore e per l'Operatore stesso."""

    queryset = Disponibilita.objects.select_related('operatore').all()
    serializer_class = DisponibilitaSerializer
    permission_classes = [read_only_or_roles_required('Amministratore', 'Operatore')]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['operatore', 'giorno_settimana']

    def perform_create(self, serializer):
        operatore = serializer.validated_data['operatore']
        self._verifica_permesso_operatore(operatore)
        serializer.save()

    def perform_update(self, serializer):
        self._verifica_permesso_operatore(serializer.instance.operatore)
        serializer.save()

    def perform_destroy(self, instance):
        self._verifica_permesso_operatore(instance.operatore)
        instance.delete()

    def _verifica_permesso_operatore(self, operatore):
        user = self.request.user
        if user.roles.filter(nome='Amministratore').exists():
            return
        if not hasattr(user, 'operatore') or user.operatore != operatore:
            raise PermissionDenied('Puoi modificare solo i tuoi turni di disponibilità.')

    @action(detail=False, methods=['post'], url_path='imposta-settimana')
    def imposta_settimana(self, request):
        """Imposta in blocco i turni settimanali per un operatore.

        Payload atteso:
        {
            "operatore": "<uuid>",
            "giorni": [
                {"giorno_settimana": 0, "ora_inizio": "09:00", "ora_fine": "18:00"},
                ...
            ]
        }
        """
        operatore_id = request.data.get('operatore')
        if not operatore_id:
            raise ValidationError({'operatore': 'ID operatore obbligatorio.'})

        try:
            operatore = Operatore.objects.get(pk=operatore_id)
        except Operatore.DoesNotExist:
            raise ValidationError({'operatore': 'Operatore non trovato.'})

        self._verifica_permesso_operatore(operatore)

        giorni = request.data.get('giorni', [])
        if not isinstance(giorni, list):
            raise ValidationError({'giorni': 'Deve essere una lista di turni.'})

        with transaction.atomic():
            # Cancella i turni esistenti per questo operatore e ricreali
            Disponibilita.objects.filter(operatore=operatore).delete()
            nuovi_turni = []
            for g in giorni:
                serializer = DisponibilitaSerializer(
                    data={
                        'operatore': operatore.id,
                        'giorno_settimana': g.get('giorno_settimana'),
                        'ora_inizio': g.get('ora_inizio'),
                        'ora_fine': g.get('ora_fine'),
                    }
                )
                serializer.is_valid(raise_exception=True)
                nuovi_turni.append(serializer.save())

        risultati = DisponibilitaSerializer(nuovi_turni, many=True).data
        return Response(risultati, status=status.HTTP_200_OK)


class EccezioneDisponibilitaViewSet(viewsets.ModelViewSet):
    """Gestione eccezioni (ferie, assenze, permessi e chiusure straordinarie).
    Lettura per tutti gli autenticati.
    Scrittura per Amministratore e per l'Operatore stesso (limitato alle proprie eccezioni).
    Le chiusure generali del salone (operatore=None) sono riservate all'Amministratore.
    """

    queryset = EccezioneDisponibilita.objects.select_related('operatore').all()
    serializer_class = EccezioneDisponibilitaSerializer
    permission_classes = [read_only_or_roles_required('Amministratore', 'Operatore')]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['operatore', 'tipo']
    search_fields = ['motivo']

    def get_queryset(self):
        qs = super().get_queryset()
        data_da = self.request.query_params.get('data_da')
        data_a = self.request.query_params.get('data_a')
        salone = self.request.query_params.get('salone')

        if data_da:
            qs = qs.filter(data_fine__gte=data_da)
        if data_a:
            qs = qs.filter(data_inizio__lte=data_a)
        if salone == 'true':
            qs = qs.filter(operatore__isnull=True)
        return qs

    def perform_create(self, serializer):
        operatore = serializer.validated_data.get('operatore')
        self._verifica_permesso(operatore)
        serializer.save()

    def perform_update(self, serializer):
        operatore = serializer.validated_data.get('operatore', serializer.instance.operatore)
        self._verifica_permesso(operatore)
        serializer.save()

    def perform_destroy(self, instance):
        self._verifica_permesso(instance.operatore)
        instance.delete()

    def _verifica_permesso(self, operatore):
        user = self.request.user
        if user.is_superuser or user.roles.filter(nome='Amministratore').exists():
            return
        if operatore is None:
            raise PermissionDenied(
                "Solo un amministratore può configurare chiusure per l'intero salone."
            )
        if not hasattr(user, 'operatore') or user.operatore != operatore:
            raise PermissionDenied('Puoi gestire solo le tue ferie e assenze.')


