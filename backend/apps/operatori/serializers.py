from rest_framework import serializers

from .models import Disponibilita, Operatore


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
