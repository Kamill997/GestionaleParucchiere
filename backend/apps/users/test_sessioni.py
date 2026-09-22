from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User, UserSession
from conftest import login_with_csrf

pytestmark = pytest.mark.django_db


@pytest.fixture
def utente_con_password():
    return User.objects.create_user(email='test-sessioni@example.com', password='password-sicura-123')


class TestSessionManagement:
    def test_login_traccia_sessione_con_dispositivo(self, api_client, utente_con_password):
        api_client.get('/api/v1/auth/csrf/')
        csrf = api_client.cookies['csrftoken'].value

        res = api_client.post(
            '/api/v1/auth/login/',
            {'email': utente_con_password.email, 'password': 'password-sicura-123'},
            HTTP_X_CSRFTOKEN=csrf,
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        )
        assert res.status_code == 200

        sessione = UserSession.objects.filter(user=utente_con_password).first()
        assert sessione is not None
        assert 'Chrome su Windows' in sessione.dispositivo
        assert not sessione.revocata

    def test_elenco_sessioni_identifica_sessione_corrente(self, utente_con_password):
        # Primo login (dispositivo 1)
        client1 = APIClient(enforce_csrf_checks=True)
        login_with_csrf(client1, utente_con_password.email, 'password-sicura-123')

        # Secondo login (dispositivo 2)
        client2 = APIClient(enforce_csrf_checks=True)
        login_with_csrf(client2, utente_con_password.email, 'password-sicura-123')

        # Richiesta da client2
        res = client2.get('/api/v1/auth/sessioni/')
        assert res.status_code == 200
        sessioni = res.data
        assert len(sessioni) == 2

        correnti = [s for s in sessioni if s['e_corrente']]
        non_correnti = [s for s in sessioni if not s['e_corrente']]
        assert len(correnti) == 1
        assert len(non_correnti) == 1

    def test_revoca_singola_sessione_inserisce_in_blacklist(self, utente_con_password):
        client1 = APIClient(enforce_csrf_checks=True)
        csrf1 = login_with_csrf(client1, utente_con_password.email, 'password-sicura-123')

        client2 = APIClient(enforce_csrf_checks=True)
        csrf2 = login_with_csrf(client2, utente_con_password.email, 'password-sicura-123')

        sessione1 = UserSession.objects.filter(user=utente_con_password).order_by('creato_il').first()

        # client2 revoca sessione1
        res = client2.post(f'/api/v1/auth/sessioni/{sessione1.id}/revoca/', HTTP_X_CSRFTOKEN=csrf2)
        assert res.status_code == 200

        sessione1.refresh_from_db()
        assert sessione1.revocata is True

        # Refresh da client1 deve fallire con 401
        res_refresh = client1.post('/api/v1/auth/refresh/', HTTP_X_CSRFTOKEN=csrf1)
        assert res_refresh.status_code == 401
        assert any(w in res_refresh.data['detail'].lower() for w in ['revocata', 'non valido', 'scaduto'])

    def test_revoca_altre_sessioni(self, utente_con_password):
        client1 = APIClient(enforce_csrf_checks=True)
        csrf1 = login_with_csrf(client1, utente_con_password.email, 'password-sicura-123')

        client2 = APIClient(enforce_csrf_checks=True)
        csrf2 = login_with_csrf(client2, utente_con_password.email, 'password-sicura-123')

        # client2 revoca le altre sessioni
        res = client2.post('/api/v1/auth/sessioni/revoca-altre/', HTTP_X_CSRFTOKEN=csrf2)
        assert res.status_code == 200

        # client1 non riesce piu' a fare refresh
        res_ref1 = client1.post('/api/v1/auth/refresh/', HTTP_X_CSRFTOKEN=csrf1)
        assert res_ref1.status_code == 401

        # client2 riesce ancora a fare refresh
        res_ref2 = client2.post('/api/v1/auth/refresh/', HTTP_X_CSRFTOKEN=csrf2)
        assert res_ref2.status_code == 200

    def test_revoca_globale_invalida_immediatamente_token_esistenti(self, utente_con_password):
        client1 = APIClient(enforce_csrf_checks=True)
        csrf1 = login_with_csrf(client1, utente_con_password.email, 'password-sicura-123')

        # Richiesta autenticata funziona
        res_me = client1.get('/api/v1/auth/me/')
        assert res_me.status_code == 200

        # Revoca globale
        res_rev = client1.post('/api/v1/auth/sessioni/revoca-tutte/', HTTP_X_CSRFTOKEN=csrf1)
        assert res_rev.status_code == 200

        utente_con_password.refresh_from_db()
        assert utente_con_password.tokens_revoked_at is not None

        # Richiesta con token emesso prima della revoca fallisce con 401
        res_me_dopo = client1.get('/api/v1/auth/me/')
        assert res_me_dopo.status_code == 401
