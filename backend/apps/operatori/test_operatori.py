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
