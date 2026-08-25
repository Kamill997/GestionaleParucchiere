from rest_framework import mixins, viewsets

from common.permissions import roles_required

from .models import DEFAULTS, Impostazione
from .serializers import ImpostazioneSerializer


class ImpostazioneViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Sola lettura + modifica (niente creazione/eliminazione: le chiavi
    sono fisse). Riservato ad Amministratore."""

    serializer_class = ImpostazioneSerializer
    permission_classes = [roles_required('Amministratore')]

    def get_queryset(self):
        for chiave, (valore_default, descrizione) in DEFAULTS.items():
            Impostazione.objects.get_or_create(
                chiave=chiave, defaults={'valore': valore_default, 'descrizione': descrizione}
            )
        return Impostazione.objects.filter(chiave__in=DEFAULTS.keys())
