from datetime import datetime, timezone as dt_timezone

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifiche.models import TipoNotifica
from apps.notifiche.services import crea_notifica, notifica_cliente
from apps.operatori.models import Operatore
from apps.servizi.models import Servizio

from .models import Prenotazione, RichiestaListaAttesa, StatoListaAttesa, StatoPrenotazione
from .serializers import (
    AndamentoProfittiSerializer,
    CancellazioneSerializer,
    KPIDashboardSerializer,
    PrenotazioneSerializer,
    ReportGuadagniSerializer,
    RichiestaListaAttesaSerializer,
    SegnaPresenzaSerializer,
    SlotDisponibileSerializer,
)
from .services import (
    calcola_andamento_profitti,
    calcola_kpi_dashboard,
    calcola_report_guadagni,
    calcola_slot,
    calcola_slot_liberi,
    processa_lista_attesa_per_cancellazione,
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
            operatore_id = self.request.query_params.get('operatore')
            if operatore_id:
                qs = qs.filter(operatore_id=operatore_id)
        elif user.roles.filter(nome='Operatore').exists() and hasattr(user, 'operatore'):
            qs = qs.filter(operatore=user.operatore)
        elif hasattr(user, 'cliente'):
            qs = qs.filter(cliente=user.cliente)
        else:
            return qs.none()

        data_da = self.request.query_params.get('data_da')
        data_a = self.request.query_params.get('data_a')
        if data_da:
            qs = qs.filter(inizio__date__gte=data_da)
        if data_a:
            qs = qs.filter(inizio__date__lte=data_a)

        return qs

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

        # Blocco 5: Se il cliente aveva una richiesta in lista d'attesa per questo servizio e data, contrassegnala come prenotata
        RichiestaListaAttesa.objects.filter(
            cliente=prenotazione.cliente,
            servizio=prenotazione.servizio,
            data=prenotazione.inizio.date(),
            stato__in=[StatoListaAttesa.IN_ATTESA, StatoListaAttesa.NOTIFICATO],
        ).update(stato=StatoListaAttesa.PRENOTATO)

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

        # Blocco 5: Notifica automatica al primo cliente idoneo in lista d'attesa
        processa_lista_attesa_per_cancellazione(prenotazione)

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

    @action(detail=True, methods=['get'], url_path='ics')
    def scarica_ics(self, request, pk=None):
        """Genera e restituisce il file iCal standard RFC 5545 (.ics) per la prenotazione."""
        prenotazione = self.get_object()
        contenuto_ics = genera_ics_prenotazione(prenotazione)
        response = HttpResponse(contenuto_ics, content_type='text/calendar; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="prenotazione-{prenotazione.id}.ics"'
        return response


def genera_ics_prenotazione(prenotazione) -> str:
    """Formatta la prenotazione secondo lo standard RFC 5545 (iCalendar)."""
    now_utc = timezone.now().astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dtstart = prenotazione.inizio.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dtend = prenotazione.fine.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    extra = list(prenotazione.servizi_aggiuntivi.all()) if hasattr(prenotazione, 'servizi_aggiuntivi') else []
    servizi_elenco = [prenotazione.servizio.nome] + [s.nome for s in extra]
    servizi_titolo = ' + '.join(servizi_elenco)

    summary = f"{servizi_titolo} - Salone"
    desc = f"Appuntamento per {servizi_titolo} con {prenotazione.operatore.nome}."
    if prenotazione.note:
        desc += f" Note: {prenotazione.note}"
    # Escape caratteri speciali RFC 5545
    desc = desc.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')

    status_map = {
        StatoPrenotazione.CONFERMATA: 'CONFIRMED',
        StatoPrenotazione.CANCELLATA: 'CANCELLED',
        StatoPrenotazione.COMPLETATA: 'CONFIRMED',
    }
    cal_status = status_map.get(prenotazione.stato, 'CONFIRMED')

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Gestionale Parrucchiere//IT',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        f'UID:prenotazione-{prenotazione.id}@gestionaleparrucchiere.local',
        f'DTSTAMP:{now_utc}',
        f'DTSTART:{dtstart}',
        f'DTEND:{dtend}',
        f'SUMMARY:{summary}',
        f'DESCRIPTION:{desc}',
        'LOCATION:Salone Parrucchiere',
        f'STATUS:{cal_status}',
        'END:VEVENT',
        'END:VCALENDAR',
    ]
    return '\r\n'.join(lines) + '\r\n'


class RichiestaListaAttesaViewSet(viewsets.ModelViewSet):
    """Gestione lista d'attesa per gli slot occupati.
    Un cliente puo' vedere e creare le proprie richieste, e annullarle.
    Lo staff puo' vedere tutte le richieste e filtrarle.
    """

    serializer_class = RichiestaListaAttesaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['stato', 'data', 'servizio', 'operatore']
    ordering_fields = ['data', 'creato_il']

    def get_queryset(self):
        user = self.request.user
        qs = RichiestaListaAttesa.objects.select_related('cliente', 'operatore', 'servizio')
        if _e_staff(user):
            return qs
        if hasattr(user, 'cliente'):
            return qs.filter(cliente=user.cliente)
        return RichiestaListaAttesa.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if _e_staff(user):
            if 'cliente' not in serializer.validated_data:
                raise serializers.ValidationError(
                    {'cliente': 'Campo obbligatorio: specificare per quale cliente si inserisce la richiesta.'}
                )
            serializer.save()
        else:
            if not hasattr(user, 'cliente'):
                raise serializers.ValidationError(
                    'Nessun profilo Cliente collegato a questo account.'
                )
            serializer.save(cliente=user.cliente)

    @action(detail=True, methods=['post'])
    def annulla(self, request, pk=None):
        richiesta = self.get_object()
        if richiesta.stato in [StatoListaAttesa.PRENOTATO, StatoListaAttesa.ANNULLATO]:
            return Response(
                {'detail': f'Non puoi annullare una richiesta in stato {richiesta.stato}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        richiesta.stato = StatoListaAttesa.ANNULLATO
        richiesta.save(update_fields=['stato'])
        return Response(RichiestaListaAttesaSerializer(richiesta).data)


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

        servizi_aggiuntivi_raw = request.query_params.get('servizi_aggiuntivi')
        durata_totale = servizio.durata_minuti
        if servizi_aggiuntivi_raw:
            extra_ids = [s.strip() for s in servizi_aggiuntivi_raw.split(',') if s.strip()]
            if extra_ids:
                servizi_extra = list(Servizio.objects.filter(pk__in=extra_ids, attivo=True))
                durata_totale += sum(s.durata_minuti for s in servizi_extra)

        payload = calcola_slot(
            operatore,
            servizio,
            giorno,
            escludi_passati=True,
            durata_totale_minuti=durata_totale,
        )
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
        e_admin = _e_amministratore(request.user)
        operatore = None
        if not e_admin:
            operatore = Operatore.objects.filter(user=request.user).first()
        data = calcola_kpi_dashboard(operatore=operatore, e_amministratore=e_admin)
        return Response(KPIDashboardSerializer(data).data)


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


class AndamentoProfittiView(APIView):
    """GET /api/v1/dashboard/andamento-profitti/?giorni=30
    Restituisce l'andamento giornaliero del fatturato per il grafico lineare
    e la ripartizione per categoria per il grafico a torta.
    Riservato agli Amministratori.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not _e_amministratore(request.user):
            return Response(
                {'detail': "Riservato all'Amministratore."}, status=status.HTTP_403_FORBIDDEN
            )
        try:
            giorni = int(request.query_params.get('giorni', 30))
            if giorni not in (7, 14, 30, 60, 90):
                giorni = 30
        except ValueError:
            giorni = 30

        data = calcola_andamento_profitti(giorni=giorni)
        return Response(AndamentoProfittiSerializer(data).data)
