from rest_framework import serializers

from common.validators import validate_image_upload
from .models import Disponibilita, EccezioneDisponibilita, Operatore


class OperatoreSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Operatore
        fields = ['id', 'user', 'email', 'nome', 'specializzazioni', 'foto', 'attivo']
        extra_kwargs = {
            # Il collegamento a uno User esistente si fa passando il suo id;
            # la creazione dello User stesso e' compito del modulo Gestione
            # Utenti & Ruoli (Fase 4, lato UI), non di questo endpoint.
            'user': {'write_only': True},
        }

    def validate_foto(self, value):
        if value:
            return validate_image_upload(value, max_size_mb=5)
        return value


class DisponibilitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disponibilita
        fields = ['id', 'operatore', 'giorno_settimana', 'ora_inizio', 'ora_fine']

    def validate(self, attrs):
        ora_inizio = attrs.get('ora_inizio') or getattr(self.instance, 'ora_inizio', None)
        ora_fine = attrs.get('ora_fine') or getattr(self.instance, 'ora_fine', None)
        if ora_fine <= ora_inizio:
            raise serializers.ValidationError(
                {'ora_fine': "Deve essere successiva all'ora di inizio."}
            )
        return attrs


class EccezioneDisponibilitaSerializer(serializers.ModelSerializer):
    operatore_nome = serializers.CharField(source='operatore.nome', read_only=True, allow_null=True)

    class Meta:
        model = EccezioneDisponibilita
        fields = [
            'id',
            'operatore',
            'operatore_nome',
            'tipo',
            'data_inizio',
            'data_fine',
            'ora_inizio',
            'ora_fine',
            'motivo',
            'creato_il',
        ]
        read_only_fields = ['creato_il']

    def validate(self, attrs):
        data_inizio = attrs.get('data_inizio') or getattr(self.instance, 'data_inizio', None)
        data_fine = attrs.get('data_fine') or getattr(self.instance, 'data_fine', None)
        if data_inizio and data_fine and data_fine < data_inizio:
            raise serializers.ValidationError(
                {'data_fine': 'La data di fine non può essere antecedente alla data di inizio.'}
            )

        ora_inizio = attrs.get('ora_inizio', getattr(self.instance, 'ora_inizio', None))
        ora_fine = attrs.get('ora_fine', getattr(self.instance, 'ora_fine', None))
        if (ora_inizio and not ora_fine) or (ora_fine and not ora_inizio):
            raise serializers.ValidationError(
                "Specificare sia ora inizio che ora fine per un'eccezione oraria, oppure lasciare entrambi vuoti per coprire l'intera giornata."
            )
        if ora_inizio and ora_fine and ora_fine <= ora_inizio:
            raise serializers.ValidationError(
                {'ora_fine': "L'ora di fine deve essere successiva all'ora di inizio."}
            )

        return attrs
