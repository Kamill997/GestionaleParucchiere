"""Test del modulo di autenticazione (Fase 2): registrazione, login/logout
via cookie httpOnly, refresh, guard RBAC su un endpoint protetto.

Stile pytest (non Django TestCase), coerente con docs/02-backend.md ("pytest
+ pytest-django, developer experience piu' moderna del test runner
integrato di Django"). Fixture condivise (api_client, cliente_utente,
admin_utente...) in backend/conftest.py.
"""

import pytest

from apps.clienti.models import Cliente
from apps.roles.models import Role

from .models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def amministratore_role():
    role, _ = Role.objects.get_or_create(nome='Amministratore')
    return role


def _get_csrf_token(client):
    response = client.get('/api/v1/auth/csrf/')
    assert response.status_code == 200
    return client.cookies['csrftoken'].value


class TestRegistrazione:
    def test_registrazione_crea_utente_con_ruolo_cliente(self, api_client):
        response = api_client.post(
            '/api/v1/auth/register/',
            {
                'email': 'cliente@example.com',
                'password': 'una-password-robusta-123',
                'nome': 'Maria',
            },
        )

        assert response.status_code == 201
        user = User.objects.get(email='cliente@example.com')
        assert user.roles.filter(nome='Cliente').exists()
        assert user.check_password('una-password-robusta-123')
        # Fase 4: la registrazione crea anche il record Cliente collegato
        assert Cliente.objects.filter(user=user, email='cliente@example.com').exists()

    def test_registrazione_rifiuta_password_debole(self, api_client):
        response = api_client.post(
            '/api/v1/auth/register/',
            {'email': 'debole@example.com', 'password': '123'},
        )
        assert response.status_code == 400


class TestLoginELogout:
    def test_login_imposta_cookie_httponly_e_niente_token_nel_body(self, api_client):
        User.objects.create_user(email='utente@example.com', password='una-password-robusta-123')

        response = api_client.post(
            '/api/v1/auth/login/',
            {'email': 'utente@example.com', 'password': 'una-password-robusta-123'},
        )

        assert response.status_code == 200
        assert response.data['email'] == 'utente@example.com'
        assert 'access' not in response.data  # niente token nel body, solo in cookie
        access_cookie = response.cookies['access_token']
        assert access_cookie['httponly'] is True
        assert 'refresh_token' in response.cookies

    def test_login_credenziali_sbagliate(self, api_client):
        User.objects.create_user(email='utente2@example.com', password='una-password-robusta-123')
        response = api_client.post(
            '/api/v1/auth/login/',
            {'email': 'utente2@example.com', 'password': 'sbagliata'},
        )
        assert response.status_code == 401

    def test_me_richiede_autenticazione(self, api_client):
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == 401

    def test_flusso_login_me_logout(self, api_client):
        User.objects.create_user(email='flusso@example.com', password='una-password-robusta-123')
        csrf_token = _get_csrf_token(api_client)

        login_response = api_client.post(
            '/api/v1/auth/login/',
            {'email': 'flusso@example.com', 'password': 'una-password-robusta-123'},
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert login_response.status_code == 200

        me_response = api_client.get('/api/v1/auth/me/')
        assert me_response.status_code == 200
        assert me_response.data['email'] == 'flusso@example.com'

        logout_response = api_client.post('/api/v1/auth/logout/', HTTP_X_CSRFTOKEN=csrf_token)
        assert logout_response.status_code == 200

        me_after_logout = api_client.get('/api/v1/auth/me/')
        assert me_after_logout.status_code == 401


class TestRefresh:
    def test_refresh_senza_cookie_restituisce_401(self, api_client):
        response = api_client.post('/api/v1/auth/refresh/')
        assert response.status_code == 401

    def test_refresh_rinnova_access_token(self, api_client):
        User.objects.create_user(email='refresh@example.com', password='una-password-robusta-123')
        csrf_token = _get_csrf_token(api_client)
        api_client.post(
            '/api/v1/auth/login/',
            {'email': 'refresh@example.com', 'password': 'una-password-robusta-123'},
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        old_access = api_client.cookies['access_token'].value

        refresh_response = api_client.post('/api/v1/auth/refresh/', HTTP_X_CSRFTOKEN=csrf_token)

        assert refresh_response.status_code == 200
        new_access = api_client.cookies['access_token'].value
        assert new_access != old_access

    def test_refresh_funziona_anche_con_access_token_scaduto_o_invalido(self, api_client):
        """Regressione: un access_token cookie invalido/scaduto non deve
        bloccare /auth/refresh/ con 401 prima ancora di eseguire la view
        (vedi common/authentication.py, gestione InvalidToken/TokenError)."""
        User.objects.create_user(email='scaduto@example.com', password='una-password-robusta-123')
        api_client.post(
            '/api/v1/auth/login/',
            {'email': 'scaduto@example.com', 'password': 'una-password-robusta-123'},
        )
        api_client.cookies['access_token'] = 'token-corrotto-o-scaduto'

        refresh_response = api_client.post('/api/v1/auth/refresh/')

        assert refresh_response.status_code == 200


class TestGuardRBAC:
    """Verifica il requisito di Fase 2: "guard RBAC funzionanti su almeno
    un endpoint protetto" (docs/05-passaggi-esecutivi.md)."""

    def test_cliente_non_accede_a_endpoint_amministratore(self, api_client):
        User.objects.create_user(
            email='solocliente@example.com', password='una-password-robusta-123'
        )
        api_client.post(
            '/api/v1/auth/login/',
            {'email': 'solocliente@example.com', 'password': 'una-password-robusta-123'},
        )

        response = api_client.get('/api/v1/admin/utenti/')
        assert response.status_code == 403

    def test_amministratore_accede_a_endpoint_amministratore(self, api_client, amministratore_role):
        admin_user = User.objects.create_user(
            email='admin@example.com', password='una-password-robusta-123'
        )
        admin_user.roles.add(amministratore_role)

        api_client.post(
            '/api/v1/auth/login/',
            {'email': 'admin@example.com', 'password': 'una-password-robusta-123'},
        )

        response = api_client.get('/api/v1/admin/utenti/')
        assert response.status_code == 200
