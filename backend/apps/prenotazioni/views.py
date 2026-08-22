from datetime import datetime

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifiche.models import TipoNotifica
from apps.notifiche.services import crea_notifica, notifica_cliente
from apps.operatori.models import Operatore
from apps.servizi.models import Servizio

from .models import Prenotazione, StatoPrenotazione
from .serializers import (
    CancellazioneSerializer,
    KPIDashboardSerializer,
    PrenotazioneSerializer,
    ReportGuadagniSerializer,
    SegnaPresenzaSerializer,
    SlotDisponibileSerializer,
)
from .services import (
    calcola_kpi_dashboard,
    calcola_report_guadagni,
    calcola_slot_liberi,
    segna_presenza,
)

STAFF_ROLES = ('Amministratore', 'Operatore')


def _e_staff(user) -> bool:
    return user.is_superuser or user.roles.filter(nome__in=STAFF_ROLES).exists()


def _e_amministratore(user) -> bool:
    return user.is_superuser or user.roles.filter(nome='Amministratore').exists()


class PrenotazioneViewSet(viewsets.ModelViewSet):
    """Amministratore vede tutte le prenotazioni; un Operatore vede solo le
    proprie; un Cliente vede solo le proprie (docs/esempio-settore-parrucchiere.md,
    "Ruoli utente" e "Gestione delle proprie prenotazioni")."""

    serializer_class = PrenotazioneSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['stato']
    ordering_fields = ['inizio']

    def get_queryset(self):
        user = self.request.user
        qs = Prenotazione.objects.select_related('cliente', 'operatore', 'servizio')
        if _e_amministratore(user):
            return qs
        if user.roles.filter(nome='Operatore').exists() and hasattr(user, 'operatore'):
            return qs.filter(operatore=user.operatore)
        if hasattr(user, 'cliente'):
            return qs.filter(cliente=user.cliente)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        # Un Cliente prenota sempre per se stesso: il campo cliente inviato
        # dal client, se diverso, viene ignorato. Lo staff (prenotazioni
        # telefoniche) puo' invece specificare qualunque cliente, ma deve
        # farlo esplicitamente: non esiste un "cliente proprio" da dedurre.
        if _e_staff(user):
            if 'cliente' not in serializer.validated_data:
                raise serializers.ValidationError(
                    {'cliente': 'Campo obbligatorio: specificare per quale cliente si prenota.'}
                )
            serializer.save()
        else:
            if not hasattr(user, 'cliente'):
                raise serializers.ValidationError(
                    'Nessun profilo Cliente collegato a questo account.'
                )
            serializer.save(cliente=user.cliente)

        prenotazione = serializer.instance
        # docs/esempio-settore-parrucchiere.md, "Notifiche specifiche del
        # settore": conferma immediata al cliente, in-app all'operatore
        # assegnato (niente email per l'operatore: la tabella dei docs
        # dice "in-app, eventualmente push", non email).
        notifica_cliente(
            prenotazione.cliente,
            TipoNotifica.CONFERMA_PRENOTAZIONE,
            'Prenotazione confermata',
            f"Il tuo appuntamento per {prenotazione.servizio.nome} e' confermato per "
            f'{prenotazione.inizio:%d/%m/%Y alle %H:%M}.',
            link='/le-mie-prenotazioni',
        )
        crea_notifica(
            prenotazione.operatore.user,
            TipoNotifica.NUOVA_PRENOTAZIONE_RICEVUTA,
            'Nuova prenotazione ricevuta',
            f'{prenotazione.cliente.nome} ha prenotato {prenotazione.servizio.nome} per '
            f'{prenotazione.inizio:%d/%m/%Y alle %H:%M}.',
            link='/gestione-prenotazioni',
        )

    @action(detail=True, methods=['post'])
    def cancella(self, request, pk=None):
        prenotazione = self.get_object()
        richiedente_e_staff = _e_staff(request.user)
        serializer = CancellazioneSerializer(
            data={},
            context={'prenotazione': prenotazione, 'richiedente_e_staff': richiedente_e_staff},
        )
        serializer.is_valid(raise_exception=True)
        prenotazione.stato = StatoPrenotazione.CANCELLATA
        prenotazione.save(update_fields=['stato'])

        # docs/esempio-settore-parrucchiere.md: "Cancellazione/modifica da
        # parte del salone -> Cliente". Notifica solo se e' lo staff a
        # cancellare: se e' il cliente stesso ad annullare, lo sa gia' (l'ha
        # appena fatto lui), non serve avvisarlo di una sua azione.
        if richiedente_e_staff:
            notifica_cliente(
                prenotazione.cliente,
                TipoNotifica.CANCELLAZIONE_PRENOTAZIONE,
                'Prenotazione cancellata dal salone',
                f'Il tuo appuntamento per {prenotazione.servizio.nome} del '
                f"{prenotazione.inizio:%d/%m/%Y alle %H:%M} e' stato cancellato dal salone. "
                'Contatta il salone per riprogrammarlo.',
                link='/le-mie-prenotazioni',
            )
        return Response(PrenotazioneSerializer(prenotazione).data)

    @action(detail=True, methods=['post'], url_path='segna-presenza')
    def segna_presenza_action(self, request, pk=None):
        """docs/08-pagamenti.md, "Tracciamento presenza": solo staff puo'
        marcare la presenza (un Cliente non deve poter segnarsi da solo
        come 'presente')."""
        if not _e_staff(request.user):
            return Response({'detail': 'Riservato allo staff.'}, status=status.HTTP_403_FORBIDDEN)
        prenotazione = self.get_object()
        serializer = SegnaPresenzaSerializer(
            data=request.data, context={'prenotazione': prenotazione}
        )
        serializer.is_valid(raise_exception=True)
        segna_presenza(
            prenotazione, serializer.validated_data['stato_presenza'], autore=request.user
        )
        return Response(PrenotazioneSerializer(prenotazione).data)


class SlotDisponibiliView(APIView):
    """GET /api/v1/slot-disponibili/?operatore=<id>&servizio=<id>&data=YYYY-MM-DD"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        operatore_id = request.query_params.get('operatore')
        servizio_id = request.query_params.get('servizio')
        data_raw = request.query_params.get('data')
        if not (operatore_id and servizio_id and data_raw):
            return Response(
                {'detail': 'Parametri richiesti: operatore, servizio, data (YYYY-MM-DD).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            giorno = datetime.strptime(data_raw, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'detail': 'Formato data non valido, atteso YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        operatore = get_object_or_404(Operatore, pk=operatore_id, attivo=True)
        servizio = get_object_or_404(Servizio, pk=servizio_id, attivo=True)

        slot = calcola_slot_liberi(operatore, servizio, giorno)
        payload = [{'inizio': inizio, 'fine': fine} for inizio, fine in slot]
        return Response(SlotDisponibileSerializer(payload, many=True).data)


class KPIDashboardView(APIView):
    """GET /api/v1/dashboard/kpi/ - riservato allo staff (docs/esempio-settore-parrucchiere.md:
    "La Dashboard avra' KPI specifici del settore"). Un Cliente ha una
    dashboard diversa (il proprio prossimo appuntamento), gestita lato
    frontend riusando PrenotazioneViewSet, non questo endpoint."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not _e_staff(request.user):
            return Response({'detail': 'Riservato allo staff.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(KPIDashboardSerializer(calcola_kpi_dashboard()).data)


class ReportGuadagniView(APIView):
    """GET /api/v1/dashboard/report-guadagni/ - docs/08-pagamenti.md,
    "Dashboard guadagni (lato Amministratore)": a differenza del
    KPIDashboardView generale (Amministratore+Operatore), il titolo della
    sezione nei docs e' esplicitamente "lato Amministratore", quindi qui
    il controllo e' piu' stretto (_e_amministratore, non _e_staff)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not _e_amministratore(request.user):
            return Response(
                {'detail': "Riservato all'Amministratore."}, status=status.HTTP_403_FORBIDDEN
            )
        return Response(ReportGuadagniSerializer(calcola_report_guadagni()).data)
