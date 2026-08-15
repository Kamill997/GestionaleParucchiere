from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.clienti.models import Cliente
from apps.operatori.models import Disponibilita, GiornoSettimana, Operatore
from apps.prenotazioni.models import Prenotazione
from apps.users.models import User

from .models import Servizio

pytestmark = pytest.mark.django_db


@pytest.fixture
def servizio():
    return Servizio.objects.create(
        nome='Taglio uomo', categoria='Taglio', durata_minuti=30, prezzo='20.00'
    )


class TestLetturaCatalogo:
    def test_cliente_vede_il_catalogo(self, api_client, cliente_utente, servizio):
        response = api_client.get('/api/v1/servizi/')
        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_anonimo_non_vede_il_catalogo(self, api_client, servizio):
        response = api_client.get('/api/v1/servizi/')
        assert response.status_code == 401

    def test_filtro_per_categoria(self, api_client, cliente_utente, servizio):
        Servizio.objects.create(nome='Colore', categoria='Colore', durata_minuti=60, prezzo='50.00')
        response = api_client.get('/api/v1/servizi/', {'categoria': 'Taglio'})
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['nome'] == 'Taglio uomo'


class TestScritturaCatalogo:
    def test_cliente_non_puo_creare_servizi(self, api_client, cliente_utente):
        response = api_client.post(
            '/api/v1/servizi/',
            {'nome': 'Nuovo', 'categoria': 'Taglio', 'durata_minuti': 30, 'prezzo': '20.00'},
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 403

    def test_amministratore_puo_creare_servizi(self, api_client, admin_utente):
        response = api_client.post(
            '/api/v1/servizi/',
            {'nome': 'Nuovo', 'categoria': 'Taglio', 'durata_minuti': 30, 'prezzo': '20.00'},
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 201
        assert Servizio.objects.filter(nome='Nuovo').exists()

    def test_elimina_servizio_senza_prenotazioni_collegate(
        self, api_client, admin_utente, servizio
    ):
        response = api_client.delete(
            f'/api/v1/servizi/{servizio.id}/', HTTP_X_CSRFTOKEN=admin_utente.csrf_token
        )
        assert response.status_code == 204
        assert not Servizio.objects.filter(id=servizio.id).exists()

    def test_elimina_servizio_con_prenotazioni_collegate_da_errore_pulito(
        self, api_client, admin_utente, servizio
    ):
        """Regressione: FK PROTECT su Prenotazione.servizio solleva
        ProtectedError, che senza common/exceptions.py darebbe un 500 invece
        di un 400 con un messaggio comprensibile (trovato in fase di revisione)."""
        op_user = User.objects.create_user(email='op-protect@example.com', password='x')
        operatore = Operatore.objects.create(user=op_user, nome='Op Protect')
        Disponibilita.objects.create(
            operatore=operatore,
            giorno_settimana=GiornoSettimana(timezone.localdate().weekday()),
            ora_inizio=time(0, 0),
            ora_fine=time(23, 59),
        )
        cliente = Cliente.objects.create(nome='Cliente Protect', email='cli-protect@example.com')
        inizio = timezone.now() + timedelta(days=1)
        Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=inizio,
            fine=inizio + timedelta(minutes=servizio.durata_minuti),
        )

        response = api_client.delete(
            f'/api/v1/servizi/{servizio.id}/', HTTP_X_CSRFTOKEN=admin_utente.csrf_token
        )
        assert response.status_code == 400
        assert 'detail' in response.data
        assert Servizio.objects.filter(id=servizio.id).exists()  # non eliminato
