from datetime import date, datetime, time, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.clienti.models import Cliente
from apps.notifiche.models import Notifica, TipoNotifica
from apps.operatori.models import Disponibilita, GiornoSettimana, Operatore
from apps.prenotazioni.models import (
    Prenotazione,
    RichiestaListaAttesa,
    StatoListaAttesa,
    StatoPrenotazione,
)
from apps.servizi.models import Servizio
from apps.users.models import User
from conftest import login_with_csrf

pytestmark = pytest.mark.django_db


def _dt(giorno: date, ora: time):
    return timezone.make_aware(datetime.combine(giorno, ora))


@pytest.fixture
def servizio():
    return Servizio.objects.create(
        nome='Taglio Uomo', categoria='Taglio', durata_minuti=30, prezzo='25.00'
    )


@pytest.fixture
def operatore():
    user = User.objects.create_user(email='op-attesa@example.com', password='password123')
    op = Operatore.objects.create(user=user, nome='Marco Barbiere')
    for g in range(7):
        Disponibilita.objects.create(
            operatore=op,
            giorno_settimana=GiornoSettimana(g),
            ora_inizio=time(9, 0),
            ora_fine=time(18, 0),
        )
    return op


@pytest.fixture
def data_futura():
    return timezone.localdate() + timedelta(days=5)


class TestListaAttesaAPI:
    def test_cliente_crea_richiesta_lista_attesa(
        self, api_client, cliente_utente, servizio, operatore, data_futura
    ):
        payload = {
            'servizio': str(servizio.id),
            'operatore': str(operatore.id),
            'data': data_futura.isoformat(),
            'ora_preferita': '10:00:00',
            'note': 'Preferibilmente mattina',
        }
        res = api_client.post(
            '/api/v1/lista-attesa/',
            payload,
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert res.status_code == 201, res.data
        assert res.data['cliente'] == cliente_utente.cliente.id
        assert res.data['stato'] == 'in_attesa'
        assert res.data['servizio_nome'] == 'Taglio Uomo'
        assert res.data['operatore_nome'] == 'Marco Barbiere'

    def test_rifiuto_data_passata(self, api_client, cliente_utente, servizio):
        payload = {
            'servizio': str(servizio.id),
            'data': (timezone.localdate() - timedelta(days=1)).isoformat(),
        }
        res = api_client.post(
            '/api/v1/lista-attesa/',
            payload,
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert res.status_code == 400
        assert 'passata' in str(res.data)

    def test_rifiuto_duplicato_attivo(
        self, api_client, cliente_utente, servizio, operatore, data_futura
    ):
        RichiestaListaAttesa.objects.create(
            cliente=cliente_utente.cliente,
            servizio=servizio,
            operatore=operatore,
            data=data_futura,
            stato=StatoListaAttesa.IN_ATTESA,
        )
        payload = {
            'servizio': str(servizio.id),
            'data': data_futura.isoformat(),
        }
        res = api_client.post(
            '/api/v1/lista-attesa/',
            payload,
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert res.status_code == 400
        assert 'già una richiesta attiva' in str(res.data)

    def test_cliente_annulla_richiesta(
        self, api_client, cliente_utente, servizio, operatore, data_futura
    ):
        richiesta = RichiestaListaAttesa.objects.create(
            cliente=cliente_utente.cliente,
            servizio=servizio,
            operatore=operatore,
            data=data_futura,
            stato=StatoListaAttesa.IN_ATTESA,
        )
        res = api_client.post(
            f'/api/v1/lista-attesa/{richiesta.id}/annulla/',
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert res.status_code == 200
        richiesta.refresh_from_db()
        assert richiesta.stato == StatoListaAttesa.ANNULLATO

    def test_visibilita_richieste_cliente_vs_admin(
        self, api_client, cliente_utente, admin_utente, servizio, data_futura
    ):
        # cliente_utente ha una richiesta
        r1 = RichiestaListaAttesa.objects.create(
            cliente=cliente_utente.cliente, servizio=servizio, data=data_futura
        )
        # un altro cliente ha una richiesta
        altro_user = User.objects.create_user(email='altro@example.com', password='password123')
        altro_cliente = Cliente.objects.create(user=altro_user, nome='Altro Cliente', email=altro_user.email)
        r2 = RichiestaListaAttesa.objects.create(
            cliente=altro_cliente, servizio=servizio, data=data_futura
        )

        # Login come cliente_utente
        client_cli = APIClient(enforce_csrf_checks=True)
        login_with_csrf(client_cli, cliente_utente.email)
        res = client_cli.get('/api/v1/lista-attesa/')
        assert res.status_code == 200
        ids = [item['id'] for item in res.data['results']]
        assert str(r1.id) in ids
        assert str(r2.id) not in ids

        # Login come admin
        client_adm = APIClient(enforce_csrf_checks=True)
        login_with_csrf(client_adm, admin_utente.email)
        res = client_adm.get('/api/v1/lista-attesa/')
        assert res.status_code == 200
        ids = [item['id'] for item in res.data['results']]
        assert str(r1.id) in ids
        assert str(r2.id) in ids


class TestNotificaAutomaticaCancellazione:
    def test_cancellazione_prenotazione_notifica_primo_in_lista(
        self, api_client, admin_utente, operatore, servizio, data_futura
    ):
        # Due clienti
        u1 = User.objects.create_user(email='u1@example.com', password='password123')
        c1 = Cliente.objects.create(user=u1, nome='Cliente Uno', email=u1.email)

        u2 = User.objects.create_user(email='u2@example.com', password='password123')
        c2 = Cliente.objects.create(user=u2, nome='Cliente Due', email=u2.email)

        # Esiste una prenotazione per c1
        prenotazione = Prenotazione.objects.create(
            cliente=c1,
            operatore=operatore,
            servizio=servizio,
            inizio=_dt(data_futura, time(10, 0)),
            fine=_dt(data_futura, time(10, 30)),
            stato=StatoPrenotazione.CONFERMATA,
        )

        # c2 in lista d'attesa per la stessa data e servizio con ora preferita 10:00
        richiesta = RichiestaListaAttesa.objects.create(
            cliente=c2,
            servizio=servizio,
            operatore=operatore,
            data=data_futura,
            ora_preferita=time(10, 0),
            stato=StatoListaAttesa.IN_ATTESA,
        )

        # Admin cancella la prenotazione di c1
        client_adm = APIClient(enforce_csrf_checks=True)
        csrf = login_with_csrf(client_adm, admin_utente.email)
        res = client_adm.post(
            f'/api/v1/prenotazioni/{prenotazione.id}/cancella/',
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert res.status_code == 200

        # Verifica stato richiesta lista attesa
        richiesta.refresh_from_db()
        assert richiesta.stato == StatoListaAttesa.NOTIFICATO
        assert richiesta.notificato_il is not None

        # Verifica notifica inviata a c2 (su u2)
        notifica = Notifica.objects.filter(
            destinatario=u2,
            tipo=TipoNotifica.DISPONIBILITA_LISTA_ATTESA,
        ).first()
        assert notifica is not None
        assert 'Taglio Uomo' in notifica.messaggio
        assert '10:00' in notifica.messaggio

    def test_prenotazione_converte_richiesta_in_prenotato(
        self, cliente_utente, operatore, servizio, data_futura
    ):
        richiesta = RichiestaListaAttesa.objects.create(
            cliente=cliente_utente.cliente,
            servizio=servizio,
            operatore=operatore,
            data=data_futura,
            stato=StatoListaAttesa.NOTIFICATO,
        )

        client_cli = APIClient(enforce_csrf_checks=True)
        csrf = login_with_csrf(client_cli, cliente_utente.email)
        payload = {
            'operatore': str(operatore.id),
            'servizio': str(servizio.id),
            'inizio': _dt(data_futura, time(10, 0)).isoformat(),
        }
        res = client_cli.post('/api/v1/prenotazioni/', payload, HTTP_X_CSRFTOKEN=csrf)
        assert res.status_code == 201

        richiesta.refresh_from_db()
        assert richiesta.stato == StatoListaAttesa.PRENOTATO
