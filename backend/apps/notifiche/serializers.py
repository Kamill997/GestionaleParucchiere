from rest_framework import serializers

from .models import Notifica


class NotificaSerializer(serializers.ModelSerializer):
    """Sola lettura: le notifiche non si creano/modificano via questa API,
    solo il sistema le genera (vedi services.py)."""

    class Meta:
        model = Notifica
        fields = ['id', 'tipo', 'titolo', 'messaggio', 'link', 'letta', 'creato_il']
        read_only_fields = fields
