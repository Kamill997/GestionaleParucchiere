from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.roles.models import Role

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Auto-registrazione: crea l'utente con ruolo iniziale 'Cliente'
    (assegnato in views.RegisterView, non qui - vedi commento la')."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    nome = serializers.CharField(source='first_name', required=False, allow_blank=True)
    cognome = serializers.CharField(source='last_name', required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'nome', 'cognome']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='first_name', read_only=True)
    cognome = serializers.CharField(source='last_name', read_only=True)
    ruoli = serializers.SlugRelatedField(
        source='roles', slug_field='nome', many=True, read_only=True
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'nome', 'cognome', 'stato', 'ruoli', 'is_staff', 'date_joined']
        read_only_fields = fields


class UserAdminSerializer(serializers.ModelSerializer):
    """Gestione utenti/ruoli lato Amministratore (docs/03-componenti-e-workflow.md:
    "CRUD utenti, assegnazione ruoli/permessi"). A differenza di
    RegisterSerializer, qui i ruoli sono scrivibili e non c'e' auto-assegnazione
    del ruolo Cliente: chi crea l'utente sceglie esplicitamente i ruoli.

    Password non richiesta in update: se omessa, resta quella esistente.
    Un invito via email (con password temporanea generata e inviata)
    resterebbe un miglioramento naturale una volta pronto il modulo
    Notifiche - per ora l'amministratore imposta la password direttamente.
    """

    nome = serializers.CharField(source='first_name', required=False, allow_blank=True)
    cognome = serializers.CharField(source='last_name', required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True, required=False, validators=[validate_password]
    )
    ruoli = serializers.SlugRelatedField(
        source='roles', slug_field='nome', many=True, queryset=Role.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'nome', 'cognome', 'stato', 'ruoli', 'password', 'date_joined']
        read_only_fields = ['date_joined']

    def validate(self, attrs):
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Obbligatoria alla creazione.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        roles = validated_data.pop('roles', [])
        user = User.objects.create_user(password=password, **validated_data)
        if roles:
            user.roles.set(roles)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        roles = validated_data.pop('roles', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        if roles is not None:
            user.roles.set(roles)
        return user
