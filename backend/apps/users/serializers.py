from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.roles.models import Role

from .models import UserSession

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Auto-registrazione: crea l'utente con ruolo iniziale 'Cliente'
    (assegnato in views.RegisterView, non qui - vedi commento la')."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    nome = serializers.CharField(source='first_name', required=False, allow_blank=True)
    cognome = serializers.CharField(source='last_name', required=False, allow_blank=True)
    telefono = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'nome', 'cognome', 'telefono']

    def create(self, validated_data):
        telefono = validated_data.pop('telefono', '')
        user = User.objects.create_user(**validated_data)
        user._telefono_registrazione = telefono
        return user


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


class UserProfileSerializer(serializers.ModelSerializer):
    """Visualizzazione e modifica del proprio profilo utente."""

    nome = serializers.CharField(source='first_name', required=False, allow_blank=True)
    cognome = serializers.CharField(source='last_name', required=False, allow_blank=True)
    telefono = serializers.CharField(required=False, allow_blank=True)
    ruoli = serializers.SlugRelatedField(
        source='roles', slug_field='nome', many=True, read_only=True
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'nome',
            'cognome',
            'telefono',
            'stato',
            'ruoli',
            'is_staff',
            'date_joined',
        ]
        read_only_fields = ['id', 'email', 'stato', 'ruoli', 'is_staff', 'date_joined']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'cliente') and instance.cliente:
            ret['telefono'] = instance.cliente.telefono or ''
        else:
            ret['telefono'] = ''
        return ret

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save(update_fields=['first_name', 'last_name'])

        nome_completo = f'{instance.first_name} {instance.last_name}'.strip() or instance.email
        if hasattr(instance, 'cliente') and instance.cliente:
            instance.cliente.nome = nome_completo
            if 'telefono' in self.initial_data:
                instance.cliente.telefono = self.initial_data['telefono']
            instance.cliente.save()

        if hasattr(instance, 'operatore') and instance.operatore:
            instance.operatore.nome = nome_completo
            instance.operatore.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Cambio password autenticato: verifica la password attuale prima di aggiornarla."""

    vecchia_password = serializers.CharField(write_only=True)
    nuova_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_vecchia_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La password attuale non è corretta.')
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['nuova_password'])
        user.save(update_fields=['password'])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Richiesta invio link di ripristino password."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Conferma reimpostazione password con token."""

    uid = serializers.CharField()
    token = serializers.CharField()
    nuova_password = serializers.CharField(write_only=True, validators=[validate_password])


class UserSessionSerializer(serializers.ModelSerializer):
    e_corrente = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            'id',
            'dispositivo',
            'ip_address',
            'user_agent',
            'creato_il',
            'ultimo_accesso',
            'revocata',
            'e_corrente',
        ]

    def get_e_corrente(self, obj) -> bool:
        current_jti = self.context.get('current_jti')
        return bool(current_jti and obj.refresh_jti == current_jti)


