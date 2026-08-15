import pytest

from apps.roles.models import Role

from .models import User

pytestmark = pytest.mark.django_db


class TestCreazioneUtenteAdmin:
    def test_amministratore_crea_utente_con_ruoli(self, api_client, admin_utente):
        operatore_role, _ = Role.objects.get_or_create(nome='Operatore')
        response = api_client.post(
            '/api/v1/admin/utenti/',
            {
                'email': 'nuovo-staff@example.com',
                'password': 'una-password-robusta-999',
                'nome': 'Nuovo',
                'cognome': 'Staff',
                'ruoli': ['Operatore'],
            },
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 201, response.data
        utente = User.objects.get(email='nuovo-staff@example.com')
        assert utente.check_password('una-password-robusta-999')
        assert list(utente.roles.all()) == [operatore_role]

    def test_password_obbligatoria_alla_creazione(self, api_client, admin_utente):
        response = api_client.post(
            '/api/v1/admin/utenti/',
            {'email': 'senza-password@example.com'},
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 400
        assert 'password' in response.data

    def test_cliente_non_puo_creare_utenti(self, api_client, cliente_utente):
        response = api_client.post(
            '/api/v1/admin/utenti/',
            {'email': 'x@example.com', 'password': 'una-password-robusta-999'},
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 403


class TestModificaUtenteAdmin:
    def test_amministratore_cambia_ruoli(self, api_client, admin_utente):
        utente = User.objects.create_user(email='da-modificare@example.com', password='x')
        ruolo, _ = Role.objects.get_or_create(nome='Operatore')

        response = api_client.patch(
            f'/api/v1/admin/utenti/{utente.id}/',
            {'ruoli': ['Operatore']},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200, response.data
        utente.refresh_from_db()
        assert list(utente.roles.all()) == [ruolo]

    def test_amministratore_disattiva_utente(self, api_client, admin_utente):
        utente = User.objects.create_user(email='da-sospendere@example.com', password='x')

        response = api_client.patch(
            f'/api/v1/admin/utenti/{utente.id}/',
            {'stato': 'sospeso'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200
        utente.refresh_from_db()
        assert utente.stato == 'sospeso'

    def test_modifica_senza_password_non_la_cancella(self, api_client, admin_utente):
        utente = User.objects.create_user(
            email='mantieni-pw@example.com', password='password-originale-123'
        )

        response = api_client.patch(
            f'/api/v1/admin/utenti/{utente.id}/',
            {'nome': 'Nome Aggiornato'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200
        utente.refresh_from_db()
        assert utente.check_password('password-originale-123')
