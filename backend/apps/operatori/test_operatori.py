import pytest

from apps.users.models import User

from .models import Operatore

pytestmark = pytest.mark.django_db


@pytest.fixture
def operatore_esistente():
    """Un Operatore collegato a un utente 'terzo', creato senza passare dal
    client di test condiviso: se dipendesse da operatore_utente (che fa
    login su api_client), autenticherebbe per sbaglio anche i test pensati
    per un visitatore anonimo."""
    titolare = User.objects.create_user(
        email='giulia@example.com', password='una-password-robusta-123'
    )
    return Operatore.objects.create(user=titolare, nome='Giulia Bianchi', specializzazioni='Colore')


class TestLetturaOperatori:
    def test_cliente_vede_elenco_operatori(self, api_client, cliente_utente, operatore_esistente):
        response = api_client.get('/api/v1/operatori/')
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['nome'] == 'Giulia Bianchi'

    def test_anonimo_non_vede_operatori(self, api_client, operatore_esistente):
        response = api_client.get('/api/v1/operatori/')
        assert response.status_code == 401


class TestScritturaOperatori:
    def test_operatore_non_puo_creare_altri_operatori(self, api_client, operatore_utente):
        secondo_user = User.objects.create_user(
            email='altro@example.com', password='una-password-robusta-123'
        )
        response = api_client.post(
            '/api/v1/operatori/',
            {'user': str(secondo_user.id), 'nome': 'Altro Operatore'},
            HTTP_X_CSRFTOKEN=operatore_utente.csrf_token,
        )
        assert response.status_code == 403

    def test_amministratore_puo_creare_operatori(self, api_client, admin_utente):
        nuovo_user = User.objects.create_user(
            email='nuovo-op@example.com', password='una-password-robusta-123'
        )
        response = api_client.post(
            '/api/v1/operatori/',
            {'user': str(nuovo_user.id), 'nome': 'Nuovo Operatore', 'specializzazioni': 'Taglio'},
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 201
        assert Operatore.objects.filter(user=nuovo_user).exists()


class TestGestioneDisponibilita:
    def test_amministratore_imposta_settimana_in_blocco(
        self, api_client, admin_utente, operatore_esistente
    ):
        payload = {
            'operatore': str(operatore_esistente.id),
            'giorni': [
                {'giorno_settimana': 0, 'ora_inizio': '09:00:00', 'ora_fine': '18:00:00'},
                {'giorno_settimana': 1, 'ora_inizio': '10:00:00', 'ora_fine': '19:00:00'},
            ],
        }
        response = api_client.post(
            '/api/v1/disponibilita/imposta-settimana/',
            payload,
            format='json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200
        assert len(response.data) == 2

        from .models import Disponibilita

        assert Disponibilita.objects.filter(operatore=operatore_esistente).count() == 2

    def test_cliente_non_puo_impostare_disponibilita(
        self, api_client, cliente_utente, operatore_esistente
    ):
        response = api_client.post(
            '/api/v1/disponibilita/imposta-settimana/',
            {
                'operatore': str(operatore_esistente.id),
                'giorni': [{'giorno_settimana': 0, 'ora_inizio': '09:00', 'ora_fine': '18:00'}],
            },
            format='json',
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 403


class TestGestioneEccezioni:
    def test_amministratore_crea_chiusura_salone(self, api_client, admin_utente):
        response = api_client.post(
            '/api/v1/eccezioni-disponibilita/',
            {
                'tipo': 'chiusura',
                'data_inizio': '2026-08-15',
                'data_fine': '2026-08-16',
                'motivo': 'Chiusura Ferragosto',
            },
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 201
        assert response.data['operatore'] is None
        assert response.data['motivo'] == 'Chiusura Ferragosto'

    def test_operatore_crea_ferie_per_se_stesso(self, api_client, operatore_utente):
        op = Operatore.objects.create(user=operatore_utente, nome='Operatore Autenticato')
        response = api_client.post(
            '/api/v1/eccezioni-disponibilita/',
            {
                'operatore': str(op.id),
                'tipo': 'ferie',
                'data_inizio': '2026-08-10',
                'data_fine': '2026-08-14',
                'motivo': 'Ferie estive',
            },
            HTTP_X_CSRFTOKEN=operatore_utente.csrf_token,
        )
        assert response.status_code == 201
        assert str(response.data['operatore']) == str(op.id)

    def test_operatore_non_puo_creare_chiusura_salone(self, api_client, operatore_utente):
        Operatore.objects.create(user=operatore_utente, nome='Operatore Autenticato')
        response = api_client.post(
            '/api/v1/eccezioni-disponibilita/',
            {
                'tipo': 'chiusura',
                'data_inizio': '2026-08-15',
                'data_fine': '2026-08-15',
                'motivo': 'Tentativo chiusura salone',
            },
            HTTP_X_CSRFTOKEN=operatore_utente.csrf_token,
        )
        assert response.status_code == 403

    def test_operatore_non_puo_impostare_ferie_altri(
        self, api_client, operatore_utente, operatore_esistente
    ):
        Operatore.objects.create(user=operatore_utente, nome='Operatore Autenticato')
        response = api_client.post(
            '/api/v1/eccezioni-disponibilita/',
            {
                'operatore': str(operatore_esistente.id),
                'tipo': 'ferie',
                'data_inizio': '2026-08-10',
                'data_fine': '2026-08-14',
            },
            HTTP_X_CSRFTOKEN=operatore_utente.csrf_token,
        )
        assert response.status_code == 403

    def test_validazione_data_fine_precedente(self, api_client, admin_utente):
        response = api_client.post(
            '/api/v1/eccezioni-disponibilita/',
            {
                'tipo': 'ferie',
                'data_inizio': '2026-08-15',
                'data_fine': '2026-08-10',
            },
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 400
        assert 'data_fine' in response.data

