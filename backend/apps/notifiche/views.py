from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notifica
from .serializers import NotificaSerializer


class NotificaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Ogni utente vede solo le proprie notifiche
    (docs/03-componenti-e-workflow.md, "Notifiche"). Sola lettura + due
    action per segnarle come lette."""

    serializer_class = NotificaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notifica.objects.filter(destinatario=self.request.user)

    @action(detail=False, methods=['get'], url_path='non-lette-count')
    def non_lette_count(self, request):
        conteggio = self.get_queryset().filter(letta=False).count()
        return Response({'conteggio': conteggio})

    @action(detail=True, methods=['post'], url_path='segna-letta')
    def segna_letta(self, request, pk=None):
        notifica = self.get_object()
        if not notifica.letta:
            notifica.letta = True
            notifica.save(update_fields=['letta'])
        return Response(NotificaSerializer(notifica).data)

    @action(detail=False, methods=['post'], url_path='segna-tutte-lette')
    def segna_tutte_lette(self, request):
        aggiornate = self.get_queryset().filter(letta=False).update(letta=True)
        return Response({'aggiornate': aggiornate})
