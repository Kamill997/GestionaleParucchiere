from rest_framework import serializers

from common.validators import validate_image_upload
from .models import Servizio


class ServizioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servizio
        fields = [
            'id',
            'nome',
            'descrizione',
            'categoria',
            'durata_minuti',
            'prezzo',
            'foto',
            'attivo',
        ]

    def validate_foto(self, value):
        if value:
            return validate_image_upload(value, max_size_mb=5)
        return value
