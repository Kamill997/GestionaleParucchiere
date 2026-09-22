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

    def test_registrazione_con_telefono_e_auto_login(self, api_client):
        response = api_client.post(
            '/api/v1/auth/register/',
            {
                'email': 'nuovocliente@example.com',
                'password': 'Password-sicura-12345',
                'nome': 'Giulia',
                'cognome': 'Rossi',
                'telefono': '3331122334',
            },
        )
        assert response.status_code == 201
        assert 'access_token' in response.cookies
        assert 'refresh_token' in response.cookies
        user = User.objects.get(email='nuovocliente@example.com')
        cliente = Cliente.objects.get(user=user)
        assert cliente.telefono == '3331122334'
        assert cliente.nome == 'Giulia Rossi'



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


class TestProfiloECambioPassword:
    def test_aggiornamento_profilo_e_sincronizzazione_cliente(self, api_client):
        user = User.objects.create_user(
            email='profilo@example.com',
            password='una-password-robusta-123',
            first_name='Luigi',
            last_name='Verdi',
        )
        Cliente.objects.create(user=user, nome='Luigi Verdi', email=user.email, telefono='111')

        api_client.post(
            '/api/v1/auth/login/',
            {'email': 'profilo@example.com', 'password': 'una-password-robusta-123'},
        )
        csrf = _get_csrf_token(api_client)

        response = api_client.patch(
            '/api/v1/auth/me/',
            {'nome': 'Luigi Mario', 'cognome': 'Verdi Rossi', 'telefono': '333444555'},
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert response.status_code == 200
        assert response.data['nome'] == 'Luigi Mario'
        assert response.data['cognome'] == 'Verdi Rossi'
        assert response.data['telefono'] == '333444555'

        user.refresh_from_db()
        assert user.first_name == 'Luigi Mario'
        assert user.cliente.nome == 'Luigi Mario Verdi Rossi'
        assert user.cliente.telefono == '333444555'

    def test_cambio_password_con_password_attuale_corretta(self, api_client):
        user = User.objects.create_user(
            email='cambiopass@example.com', password='vecchia-password-sicura-123'
        )
        api_client.post(
            '/api/v1/auth/login/',
            {'email': 'cambiopass@example.com', 'password': 'vecchia-password-sicura-123'},
        )
        csrf = _get_csrf_token(api_client)

        response = api_client.post(
            '/api/v1/auth/change-password/',
            {
                'vecchia_password': 'vecchia-password-sicura-123',
                'nuova_password': 'nuova-password-robusta-456',
            },
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password('nuova-password-robusta-456')

    def test_cambio_password_rifiuta_password_attuale_errata(self, api_client):
        user = User.objects.create_user(
            email='cambiopasserr@example.com', password='vecchia-password-sicura-123'
        )
        api_client.post(
            '/api/v1/auth/login/',
            {'email': 'cambiopasserr@example.com', 'password': 'vecchia-password-sicura-123'},
        )
        csrf = _get_csrf_token(api_client)

        response = api_client.post(
            '/api/v1/auth/change-password/',
            {
                'vecchia_password': 'password-sbagliata',
                'nuova_password': 'nuova-password-robusta-456',
            },
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert response.status_code == 400
        assert 'vecchia_password' in response.data


class TestResetPassword:
    def test_flusso_completo_reset_password(self, api_client, mailoutbox):
        user = User.objects.create_user(
            email='dimenticato@example.com', password='password-originale-123'
        )
        csrf = _get_csrf_token(api_client)

        # 1. Richiesta reset
        response = api_client.post(
            '/api/v1/auth/password-reset/',
            {'email': 'dimenticato@example.com'},
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert response.status_code == 200
        assert len(mailoutbox) == 1
        assert 'Reimposta la tua password' in mailoutbox[0].subject
        email_body = mailoutbox[0].body
        assert 'uid=' in email_body
        assert 'token=' in email_body

        # Estrai uid e token dal corpo email
        import re

        match = re.search(r'uid=([^&\s]+)&token=([^&\s]+)', email_body)
        assert match is not None
        uid = match.group(1)
        token = match.group(2)

        # 2. Conferma reset con nuova password
        response_confirm = api_client.post(
            '/api/v1/auth/password-reset-confirm/',
            {
                'uid': uid,
                'token': token,
                'nuova_password': 'password-nuova-di-zecca-789',
            },
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert response_confirm.status_code == 200

        user.refresh_from_db()
        assert user.check_password('password-nuova-di-zecca-789')

    def test_reset_password_rifiuta_token_invalido(self, api_client):
        csrf = _get_csrf_token(api_client)
        response = api_client.post(
            '/api/v1/auth/password-reset-confirm/',
            {
                'uid': 'invalid-uid',
                'token': 'invalid-token',
                'nuova_password': 'password-nuova-di-zecca-789',
            },
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert response.status_code == 400


class TestLoginRateLimitESecurityHeaders:
    def test_security_headers_presenti(self, api_client):
        response = api_client.get('/api/v1/auth/csrf/')
        assert response.status_code == 200
        assert 'Content-Security-Policy' in response
        assert "default-src 'self'" in response['Content-Security-Policy']
        assert response['X-Content-Type-Options'] == 'nosniff'
        assert response['Referrer-Policy'] == 'strict-origin-when-cross-origin'
        assert 'Permissions-Policy' in response

    def test_rate_limit_sul_login(self, api_client, monkeypatch):
        from django.core.cache import cache
        from rest_framework.settings import api_settings

        cache.clear()
        rates = dict(api_settings.DEFAULT_THROTTLE_RATES)
        rates['login'] = '2/min'
        monkeypatch.setattr(api_settings, 'DEFAULT_THROTTLE_RATES', rates)

        User.objects.create_user(email='test-throttle@example.com', password='password-sicura-123')
        csrf = _get_csrf_token(api_client)

        r1 = api_client.post(
            '/api/v1/auth/login/',
            {'email': 'test-throttle@example.com', 'password': 'errata'},
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert r1.status_code == 401

        r2 = api_client.post(
            '/api/v1/auth/login/',
            {'email': 'test-throttle@example.com', 'password': 'errata'},
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert r2.status_code == 401

        r3 = api_client.post(
            '/api/v1/auth/login/',
            {'email': 'test-throttle@example.com', 'password': 'errata'},
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert r3.status_code == 429
        cache.clear()

    def test_csrf_origin_consentito_da_frontend_vite(self, api_client):
        user = User.objects.create_user(
            email='csrf-origin@example.com', password='password-sicura-123'
        )
        api_client.post(
            '/api/v1/auth/login/',
            {'email': 'csrf-origin@example.com', 'password': 'password-sicura-123'},
        )
        csrf = _get_csrf_token(api_client)
        response = api_client.patch(
            '/api/v1/auth/me/',
            {'nome': 'Nuovo Nome'},
            HTTP_X_CSRFTOKEN=csrf,
            HTTP_ORIGIN='http://localhost:5173',
        )
        assert response.status_code == 200

    def test_csrf_origin_sconosciuto_rifiutato(self, api_client):
        user = User.objects.create_user(
            email='csrf-untrusted@example.com', password='password-sicura-123'
        )
        api_client.post(
            '/api/v1/auth/login/',
            {'email': 'csrf-untrusted@example.com', 'password': 'password-sicura-123'},
        )
        csrf = _get_csrf_token(api_client)
        response = api_client.patch(
            '/api/v1/auth/me/',
            {'nome': 'Nuovo Nome'},
            HTTP_X_CSRFTOKEN=csrf,
            HTTP_ORIGIN='http://malicious-site.example.com',
        )
        assert response.status_code == 403
        assert 'Controllo CSRF fallito' in response.data.get('detail', '')


