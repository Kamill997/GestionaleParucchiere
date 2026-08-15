from rest_framework import serializers

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
