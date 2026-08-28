from django.conf import settings
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

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


class PushSubscribeView(APIView):
    """POST /api/v1/notifiche/push-subscribe/: salva o aggiorna la
    sottoscrizione Web Push del browser. Idempotente per endpoint: se il
    browser chiama di nuovo con lo stesso endpoint (es. page refresh senza
    revocare il permesso) aggiorna subscription_data invece di creare un
    duplicato."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        subscription_data = request.data.get('subscription')
        if not subscription_data or 'endpoint' not in subscription_data:
            return Response({'detail': 'subscription con endpoint obbligatorio.'}, status=400)

        from .models import PushSubscription

        PushSubscription.objects.update_or_create(
            endpoint=subscription_data['endpoint'],
            defaults={'utente': request.user, 'subscription_data': subscription_data},
        )
        return Response({'detail': 'Sottoscrizione salvata.'})


class VapidPublicKeyView(APIView):
    """Chiave pubblica VAPID: il browser ne ha bisogno per creare una
    PushSubscription. Non e' un segreto (la chiave PRIVATA lo e')."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        public_key = getattr(settings, 'VAPID_PUBLIC_KEY', '')
        if not public_key:
            return Response({'detail': 'Push non configurato.'}, status=501)
        return Response({'public_key': public_key})
