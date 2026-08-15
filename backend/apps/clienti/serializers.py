from rest_framework import serializers

from .models import Cliente

STAFF_ROLES = ('Amministratore', 'Operatore')


class ClienteSerializer(serializers.ModelSerializer):
    """note_preferenze sono note interne, esplicitamente "non visibili al
    cliente" (docs/esempio-settore-parrucchiere.md, "Funzionalita' lato
    Amministratore/Staff" -> "Gestione clienti"): un Cliente vede il proprio
    record (nome/email/telefono) ma non queste note, ne' puo' scriverle.
    """

    class Meta:
        model = Cliente
        fields = [
            'id',
            'user',
            'nome',
            'email',
            'telefono',
            'note_preferenze',
            'bloccato',
            'contatore_no_show',
        ]
        extra_kwargs = {
            'user': {'read_only': True},  # collegato automaticamente alla registrazione (Fase 2)
        }
        read_only_fields = ['bloccato', 'contatore_no_show']

    def _richiedente_e_staff(self) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        user = request.user
        return user.is_superuser or user.roles.filter(nome__in=STAFF_ROLES).exists()

    def to_representation(self, instance):
        rappresentazione = super().to_representation(instance)
        if not self._richiedente_e_staff():
            rappresentazione.pop('note_preferenze', None)
        return rappresentazione

    def validate(self, attrs):
        if 'note_preferenze' in self.initial_data and not self._richiedente_e_staff():
            raise serializers.ValidationError(
                {'note_preferenze': 'Solo lo staff può leggere o modificare le note interne.'}
            )
        return super().validate(attrs)
