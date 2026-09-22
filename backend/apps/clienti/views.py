from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit_log.models import AuditLog
from apps.prenotazioni.services import sblocca_cliente

from common.validators import validate_document_upload
from rest_framework.exceptions import ValidationError
from .import_export import (
    ESTENSIONI_CONSENTITE,
    MAX_FILE_SIZE_BYTES,
    esporta_clienti_csv,
    genera_template_csv,
    importa_clienti,
)
from .models import Cliente
from .serializers import ClienteSerializer

STAFF_ROLES = ('Amministratore', 'Operatore')


def _e_amministratore(user) -> bool:
    return user.is_superuser or user.roles.filter(nome='Amministratore').exists()


class ClienteViewSet(viewsets.ModelViewSet):
    """Anagrafica clienti: dati potenzialmente sensibili (note_preferenze
    puo' contenere dati sanitari, vedi docs/esempio-settore-parrucchiere.md
    "Nota" sul GDPR). Staff (Amministratore/Operatore) vede tutti i clienti;
    un utente con solo ruolo Cliente vede esclusivamente il proprio record.
    """

    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['nome', 'email', 'telefono']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.roles.filter(nome__in=STAFF_ROLES).exists():
            return Cliente.objects.all()
        return Cliente.objects.filter(user=user)

    @action(detail=True, methods=['post'])
    def sblocca(self, request, pk=None):
        """docs/08-pagamenti.md: "va previsto uno sblocco manuale da parte
        dell'amministratore" - esplicitamente Amministratore, non
        Operatore generico."""
        user = request.user
        if not (user.is_superuser or user.roles.filter(nome='Amministratore').exists()):
            return Response(
                {'detail': "Riservato all'Amministratore."}, status=status.HTTP_403_FORBIDDEN
            )
        cliente = self.get_object()
        sblocca_cliente(cliente, autore=user)
        return Response(ClienteSerializer(cliente, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path='template-import')
    def template_import(self, request):
        """docs/07-import-export-dati.md, "Template di importazione":
        CSV scaricabile con le intestazioni corrette + una riga di esempio.
        Riservato ad Amministratore, come importa/esporta sotto (vedi
        stato-avanzamento.md, "Permessi": import/export riservati ad
        Amministratore anche se la gestione clienti e' staff-wide)."""
        if not _e_amministratore(request.user):
            return Response(
                {'detail': "Riservato all'Amministratore."}, status=status.HTTP_403_FORBIDDEN
            )
        response = HttpResponse(genera_template_csv(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="template-clienti.csv"'
        return response

    @action(detail=False, methods=['post'])
    def importa(self, request):
        """docs/07-import-export-dati.md, import in blocco. Scope ridotto
        dichiarato in stato-avanzamento.md: elaborazione sincrona (niente
        Celery), colonne fisse da template (niente mappatore interattivo).

        Niente parser_classes esplicito: DRF include gia' MultiPartParser
        di default (lezione gia' imparata una volta su questo stesso
        endpoint, vedi stato-avanzamento.md).
        """
        if not _e_amministratore(request.user):
            return Response(
                {'detail': "Riservato all'Amministratore."}, status=status.HTTP_403_FORBIDDEN
            )

        file_obj = request.FILES.get('file')
        if file_obj is None:
            return Response(
                {'detail': 'Nessun file caricato (campo atteso: "file").'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        nome_file = file_obj.name
        try:
            validate_document_upload(file_obj, max_size_mb=5)
            report = importa_clienti(file_obj, nome_file, request=request)
        except ValidationError as e:
            msg = e.detail[0] if isinstance(e.detail, list) else str(e.detail)
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {'detail': 'File non leggibile: verifica che sia un CSV/Excel valido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # docs/07-import-export-dati.md, "Sicurezza": "un'esportazione di
        # massa di dati personali e' un evento rilevante anche ai fini
        # della protezione dei dati" - vale anche per l'import in blocco.
        AuditLog.objects.create(
            user=request.user,
            azione='clienti_importati',
            entita_coinvolta='Cliente',
            dettagli={
                'file': nome_file,
                'creati': report['creati'],
                'aggiornati': report['aggiornati'],
                'errori': len(report['errori']),
                'duplicati_interni': len(report['duplicati_interni']),
            },
        )
        return Response(report)

    @action(detail=False, methods=['get'])
    def esporta(self, request):
        """docs/07-import-export-dati.md, "Flusso di esportazione":
        rispetta i filtri/ricerca attivi sulla tabella corrente (esporta
        "quello che vedo", non sempre l'intero dataset) - riusa lo stesso
        SearchFilter gia' configurato sul viewset per la lista."""
        if not _e_amministratore(request.user):
            return Response(
                {'detail': "Riservato all'Amministratore."}, status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.filter_queryset(self.get_queryset())
        contenuto = esporta_clienti_csv(queryset)

        AuditLog.objects.create(
            user=request.user,
            azione='clienti_esportati',
            entita_coinvolta='Cliente',
            dettagli={'conteggio': queryset.count()},
        )

        response = HttpResponse(contenuto, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clienti-esportati.csv"'
        return response
