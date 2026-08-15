from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from common.permissions import read_only_or_roles_required

from .models import Servizio
from .serializers import ServizioSerializer


class ServizioViewSet(viewsets.ModelViewSet):
    """Catalogo servizi: lettura per chiunque sia autenticato (Cliente incluso,
    deve poter sfogliare il listino), scrittura riservata all'Amministratore."""

    queryset = Servizio.objects.all()
    serializer_class = ServizioSerializer
    permission_classes = [read_only_or_roles_required('Amministratore')]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'attivo']
    search_fields = ['nome', 'descrizione']
    ordering_fields = ['nome', 'prezzo', 'durata_minuti', 'categoria']
