from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.clienti.models import Cliente
from apps.roles.models import Role
from common.permissions import roles_required

from .models import User
from .serializers import RegisterSerializer, UserAdminSerializer, UserSerializer

_COOKIE_KW = {
    'httponly': True,
    'secure': settings.AUTH_COOKIE_SECURE,
    'samesite': settings.AUTH_COOKIE_SAMESITE,
}


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

    def perform_create(self, serializer):
        user = serializer.save()
        cliente_role, _ = Role.objects.get_or_create(nome='Cliente')
        user.roles.add(cliente_role)
        Cliente.objects.create(
            user=user,
            nome=f'{user.first_name} {user.last_name}'.strip() or user.email,
            email=user.email,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = Response(UserSerializer(serializer.user).data)
        _set_auth_cookies(
            response,
            serializer.validated_data['access'],
            serializer.validated_data['refresh'],
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

        response = Response({'detail': 'Token aggiornato.'})
        _set_auth_cookies(response, refresh.access_token)
        return response


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except TokenError:
                pass  # token gia' scaduto/invalido: nulla da revocare

        response = Response({'detail': 'Logout effettuato.'})
        response.delete_cookie(settings.AUTH_COOKIE_ACCESS, path='/')
        response.delete_cookie(settings.AUTH_COOKIE_REFRESH, path=settings.AUTH_COOKIE_REFRESH_PATH)
        return response


class CsrfCookieView(APIView):
    """Da chiamare una volta all'avvio della SPA per ricevere il cookie
    csrftoken da rimandare come header X-CSRFToken nelle richieste mutanti
    (vedi common/authentication.py)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        get_token(request)
        return Response({'detail': 'Cookie CSRF impostato.'})


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


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
