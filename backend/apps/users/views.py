from django.conf import settings
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.clienti.models import Cliente
from apps.roles.models import Role
from common.permissions import roles_required
from common.throttling import LoginRateThrottle, PasswordResetRateThrottle, RegisterRateThrottle

from .models import User, UserSession, analizza_user_agent
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserAdminSerializer,
    UserProfileSerializer,
    UserSerializer,
    UserSessionSerializer,
)

_COOKIE_KW = {
    'httponly': True,
    'secure': settings.AUTH_COOKIE_SECURE,
    'samesite': settings.AUTH_COOKIE_SAMESITE,
}


def _ottieni_client_ip(request) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'


def _set_auth_cookies(response, access, refresh=None):
    response.set_cookie(
        settings.AUTH_COOKIE_ACCESS,
        str(access),
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        path='/',
        **_COOKIE_KW,
    )
    if refresh is not None:
        response.set_cookie(
            settings.AUTH_COOKIE_REFRESH,
            str(refresh),
            max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            path=settings.AUTH_COOKIE_REFRESH_PATH,
            **_COOKIE_KW,
        )


class RegisterView(generics.CreateAPIView):
    """Auto-registrazione pubblica: nuovo utente con ruolo 'Cliente' di default.

    Staff (Operatore/Amministratore) va creato/promosso da un amministratore
    (Django Admin o, in futuro, il modulo Gestione Utenti & Ruoli lato UI),
    non tramite questo endpoint pubblico.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterRateThrottle]

    def perform_create(self, serializer):
        user = serializer.save()
        cliente_role, _ = Role.objects.get_or_create(nome='Cliente')
        user.roles.add(cliente_role)
        telefono = getattr(user, '_telefono_registrazione', '')
        Cliente.objects.create(
            user=user,
            nome=f'{user.first_name} {user.last_name}'.strip() or user.email,
            email=user.email,
            telefono=telefono,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user = serializer.instance
        refresh = RefreshToken.for_user(user)

        # Blocco 6: Traccia la sessione attiva
        ip = _ottieni_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')
        dispositivo = analizza_user_agent(ua)
        UserSession.objects.create(
            user=user,
            refresh_jti=refresh['jti'],
            ip_address=ip,
            user_agent=ua[:512],
            dispositivo=dispositivo,
        )

        response = Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        _set_auth_cookies(response, refresh.access_token, refresh)
        return response


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        refresh_raw = serializer.validated_data['refresh']
        refresh = RefreshToken(refresh_raw)

        # Blocco 6: Traccia la sessione attiva
        ip = _ottieni_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')
        dispositivo = analizza_user_agent(ua)
        UserSession.objects.create(
            user=user,
            refresh_jti=refresh['jti'],
            ip_address=ip,
            user_agent=ua[:512],
            dispositivo=dispositivo,
        )

        response = Response(UserSerializer(user).data)
        _set_auth_cookies(
            response,
            serializer.validated_data['access'],
            refresh_raw,
        )
        return response


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if raw_refresh is None:
            return Response(
                {'detail': 'Refresh token mancante.'}, status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            refresh = RefreshToken(raw_refresh)
        except TokenError:
            return Response(
                {'detail': 'Refresh token non valido o scaduto.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Blocco 6: Verifica se la sessione o i token sono stati revocati
        jti = refresh.get('jti')
        sessione = UserSession.objects.filter(refresh_jti=jti).first()
        if sessione:
            if sessione.revocata:
                return Response(
                    {'detail': 'Sessione revocata. Effettua nuovamente il login.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if sessione.user.tokens_revoked_at:
                iat = refresh.get('iat')
                if iat and iat < sessione.user.tokens_revoked_at.timestamp():
                    return Response(
                        {'detail': 'Sessione revocata. Effettua nuovamente il login.'},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            sessione.ultimo_accesso = timezone.now()
            sessione.save(update_fields=['ultimo_accesso'])

        response = Response({'detail': 'Token aggiornato.'})
        _set_auth_cookies(response, refresh.access_token)
        return response


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if raw_refresh:
            try:
                r = RefreshToken(raw_refresh)
                r.blacklist()
                UserSession.objects.filter(refresh_jti=r.get('jti')).update(
                    revocata=True, revocata_il=timezone.now()
                )
            except TokenError:
                pass  # token gia' scaduto/invalido: nulla da revocare

        response = Response({'detail': 'Logout effettuato.'})
        response.delete_cookie(
            settings.AUTH_COOKIE_ACCESS,
            path='/',
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )
        response.delete_cookie(
            settings.AUTH_COOKIE_REFRESH,
            path=settings.AUTH_COOKIE_REFRESH_PATH,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )
        return response


class CsrfCookieView(APIView):
    """Da chiamare una volta all'avvio della SPA per ricevere il cookie
    csrftoken da rimandare come header X-CSRFToken nelle richieste mutanti
    (vedi common/authentication.py)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = get_token(request)
        return Response({'csrfToken': token, 'detail': 'Cookie CSRF impostato.'})


class MeView(generics.RetrieveUpdateAPIView):
    """Visualizzazione e modifica del profilo utente corrente."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Cambio password per l'utente autenticato."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password aggiornata con successo.'})


class PasswordResetRequestView(APIView):
    """Richiesta di invio email con link per reimpostare la password dimenticata."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()

        #docs/06-security.md: per prevenire email enumeration, restituiamo sempre 200
        msg_standard = (
            'Se l\'indirizzo email è registrato, riceverai a breve un link '
            'per reimpostare la tua password.'
        )

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
            reset_link = f'{frontend_url}/reset-password?uid={uid}&token={token}'

            send_mail(
                subject='Reimposta la tua password - Salone',
                message=(
                    f'Ciao {user.first_name or user.email},\n\n'
                    'Abbiamo ricevuto una richiesta di reimpostazione della tua password.\n'
                    f'Per procedere, clicca sul link seguente:\n{reset_link}\n\n'
                    'Se non hai richiesto tu questa modifica, puoi ignorare questo messaggio.\n'
                    'Il link scadrà a breve.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        return Response({'detail': msg_standard})


class PasswordResetConfirmView(APIView):
    """Conferma reimpostazione password tramite UID e token sicuro."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid_b64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        nuova_password = serializer.validated_data['nuova_password']

        try:
            uid = force_str(urlsafe_base64_decode(uid_b64))
            user = User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Il link di recupero non è valido o è scaduto.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'detail': 'Il link di recupero non è valido o è scaduto.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(nuova_password)
        user.save(update_fields=['password'])
        return Response({'detail': 'Password reimpostata con successo. Ora puoi accedere.'})


class UserAdminViewSet(viewsets.ModelViewSet):
    """Gestione utenti/ruoli, riservata al ruolo Amministratore
    (docs/03-componenti-e-workflow.md: "CRUD utenti, assegnazione
    ruoli/permessi"). Anche il guard RBAC dimostrato per Fase 2
    (docs/05-passaggi-esecutivi.md: "Guard RBAC funzionanti su almeno un
    endpoint protetto")."""

    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [roles_required('Amministratore')]

    def get_serializer_class(self):
        return UserSerializer if self.action in ('list', 'retrieve') else UserAdminSerializer


class UserSessionViewSet(viewsets.ViewSet):
    """Gestione delle sessioni attive dell'utente autenticato (Blocco 6: Session Management).
    Permette di visualizzare tutti i dispositivi connessi, la sessione corrente,
    e revocare sessioni singole o globali.
    """

    permission_classes = [permissions.IsAuthenticated]

    def _get_current_jti(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if raw_refresh:
            try:
                return RefreshToken(raw_refresh).get('jti')
            except TokenError:
                pass
        return None

    def list(self, request):
        """GET /api/v1/auth/sessioni/ - Restituisce tutte le sessioni attive dell'utente."""
        sessioni = UserSession.objects.filter(user=request.user, revocata=False)
        current_jti = self._get_current_jti(request)
        serializer = UserSessionSerializer(sessioni, many=True, context={'current_jti': current_jti})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def revoca(self, request, pk=None):
        """POST /api/v1/auth/sessioni/{id}/revoca/ - Revoca una specifica sessione."""
        sessione = get_object_or_404(UserSession, pk=pk, user=request.user)
        if not sessione.revocata:
            sessione.revocata = True
            sessione.revocata_il = timezone.now()
            sessione.save(update_fields=['revocata', 'revocata_il'])

            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )

            out_token = OutstandingToken.objects.filter(jti=sessione.refresh_jti).first()
            if out_token:
                BlacklistedToken.objects.get_or_create(token=out_token)

        current_jti = self._get_current_jti(request)
        response = Response({'detail': 'Sessione revocata con successo.'})
        if current_jti and sessione.refresh_jti == current_jti:
            response.delete_cookie(
                settings.AUTH_COOKIE_ACCESS, path='/', samesite=settings.AUTH_COOKIE_SAMESITE
            )
            response.delete_cookie(
                settings.AUTH_COOKIE_REFRESH,
                path=settings.AUTH_COOKIE_REFRESH_PATH,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )
        return response

    @action(detail=False, methods=['post'], url_path='revoca-altre')
    def revoca_altre(self, request):
        """POST /api/v1/auth/sessioni/revoca-altre/ - Revoca tutte le sessioni tranne quella attuale."""
        current_jti = self._get_current_jti(request)
        qs = UserSession.objects.filter(user=request.user, revocata=False)
        if current_jti:
            qs = qs.exclude(refresh_jti=current_jti)

        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        jtis = list(qs.values_list('refresh_jti', flat=True))
        qs.update(revocata=True, revocata_il=timezone.now())

        for out_token in OutstandingToken.objects.filter(jti__in=jtis):
            BlacklistedToken.objects.get_or_create(token=out_token)

        return Response({'detail': 'Tutte le altre sessioni sono state revocate.'})

    @action(detail=False, methods=['post'], url_path='revoca-tutte')
    def revoca_tutte(self, request):
        """POST /api/v1/auth/sessioni/revoca-tutte/ - Revoca globale immediata di tutte le sessioni dell'utente."""
        request.user.tokens_revoked_at = timezone.now()
        request.user.save(update_fields=['tokens_revoked_at'])

        qs = UserSession.objects.filter(user=request.user, revocata=False)
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        jtis = list(qs.values_list('refresh_jti', flat=True))
        qs.update(revocata=True, revocata_il=timezone.now())

        for out_token in OutstandingToken.objects.filter(jti__in=jtis):
            BlacklistedToken.objects.get_or_create(token=out_token)

        response = Response({'detail': 'Tutte le sessioni sono state revocate.'})
        response.delete_cookie(
            settings.AUTH_COOKIE_ACCESS, path='/', samesite=settings.AUTH_COOKIE_SAMESITE
        )
        response.delete_cookie(
            settings.AUTH_COOKIE_REFRESH,
            path=settings.AUTH_COOKIE_REFRESH_PATH,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )
        return response
