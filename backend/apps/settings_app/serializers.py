from rest_framework import serializers

from .models import DEFAULTS, Impostazione


class ImpostazioneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impostazione
        fields = ['id', 'chiave', 'valore', 'descrizione']
        read_only_fields = ['id', 'chiave', 'descrizione']

    def validate_valore(self, value):
        if self.instance and self.instance.chiave in DEFAULTS:
            try:
                numero = int(value)
            except ValueError as exc:
                raise serializers.ValidationError('Deve essere un numero intero.') from exc
            if numero < 0:
                raise serializers.ValidationError('Non può essere negativo.')
        return value
