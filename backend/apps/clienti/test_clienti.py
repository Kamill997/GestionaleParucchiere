import pytest

from apps.users.models import User

from .models import Cliente

pytestmark = pytest.mark.django_db


@pytest.fixture
def cliente_ospite():
    """Cliente senza account (prenotazione da ospite, vedi docs/08-pagamenti.md)."""
    return Cliente.objects.create(
        nome='Cliente Ospite', email='ospite@example.com', telefono='333123456'
    )


class TestScopingClienti:
    def test_cliente_vede_solo_il_proprio_record(self, api_client, cliente_utente, cliente_ospite):
        # cliente_utente ha gia' un record Cliente creato dalla registrazione (Fase 2/4)
        response = api_client.get('/api/v1/clienti/')
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['email'] == cliente_utente.email

    def test_amministratore_vede_tutti_i_clienti(self, api_client, admin_utente, cliente_ospite):
        altro_utente = User.objects.create_user(
            email='altro-cliente@example.com', password='una-password-robusta-123'
        )
        Cliente.objects.create(user=altro_utente, nome='Altro Cliente', email=altro_utente.email)

        response = api_client.get('/api/v1/clienti/')
        assert response.status_code == 200
        # altro_utente + cliente_ospite (admin_utente stesso non ha un proprio record Cliente)
        assert response.data['count'] == 2

    def test_operatore_vede_tutti_i_clienti(self, api_client, operatore_utente, cliente_ospite):
        response = api_client.get('/api/v1/clienti/')
        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_cliente_non_vede_record_di_un_altro_cliente(
        self, api_client, cliente_utente, cliente_ospite
    ):
        response = api_client.get(f'/api/v1/clienti/{cliente_ospite.id}/')
        assert (
            response.status_code == 404
        )  # fuori dal proprio queryset: 404, non 403 (non se ne rivela l'esistenza)


class TestRegistrazioneCreaCliente:
    def test_ogni_registrazione_ha_il_proprio_cliente(self, api_client):
        User.objects.create_user(email='a@example.com', password='una-password-robusta-123')
        assert (
            Cliente.objects.filter(email='a@example.com').count() == 0
        )  # creato solo via endpoint register

        api_client.post(
            '/api/v1/auth/register/',
            {'email': 'b@example.com', 'password': 'una-password-robusta-123', 'nome': 'Bruno'},
        )
        cliente = Cliente.objects.get(email='b@example.com')
        assert cliente.nome == 'Bruno'


class TestNotePreferenzeRiservateAlloStaff:
    """note_preferenze sono note interne, esplicitamente 'non visibili al
    cliente' (docs/esempio-settore-parrucchiere.md)."""

    def test_cliente_non_vede_le_proprie_note_preferenze(self, api_client, cliente_utente):
        cliente_utente.cliente.note_preferenze = 'Nota interna riservata'
        cliente_utente.cliente.save(update_fields=['note_preferenze'])

        response = api_client.get(f'/api/v1/clienti/{cliente_utente.cliente.id}/')

        assert response.status_code == 200
        assert 'note_preferenze' not in response.data

    def test_amministratore_vede_le_note_preferenze(self, api_client, admin_utente, cliente_ospite):
        cliente_ospite.note_preferenze = 'Nota interna riservata'
        cliente_ospite.save(update_fields=['note_preferenze'])

        response = api_client.get(f'/api/v1/clienti/{cliente_ospite.id}/')

        assert response.status_code == 200
        assert response.data['note_preferenze'] == 'Nota interna riservata'

    def test_cliente_non_puo_scrivere_le_proprie_note_preferenze(self, api_client, cliente_utente):
        csrf_token = cliente_utente.csrf_token
        response = api_client.patch(
            f'/api/v1/clienti/{cliente_utente.cliente.id}/',
            {'note_preferenze': 'Provo a scrivere'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 400
