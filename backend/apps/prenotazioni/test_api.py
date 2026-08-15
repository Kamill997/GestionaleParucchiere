from datetime import date, datetime, time, timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.clienti.models import Cliente
from apps.operatori.models import Disponibilita, GiornoSettimana, Operatore
from apps.servizi.models import Servizio
from apps.users.models import User

from .models import Prenotazione, StatoPrenotazione

pytestmark = pytest.mark.django_db


def _dt(giorno: date, ora: time):
    return timezone.make_aware(datetime.combine(giorno, ora))


@pytest.fixture
def martedi_prossimo():
    """Il prossimo martedi' con ALMENO 48 ore di margine da adesso.

    Bug reale osservato: "prossimo martedi'" calcolato sul solo giorno di
    calendario puo' risultare a sole 15 ore di distanza se il test gira di
    lunedi' sera (un giorno di calendario avanti, ma non 24 ore vere) -
    abbastanza per far fallire per davvero test sulla policy di
    cancellazione (soglia 24h) in modo dipendente dall'orario di esecuzione.
    """
    ora = timezone.now()
    giorni_al_martedi = (1 - ora.weekday()) % 7 or 7
    candidato = ora.date() + timedelta(days=giorni_al_martedi)
    inizio_candidato = timezone.make_aware(datetime.combine(candidato, time(10, 0)))
    if inizio_candidato - ora < timedelta(hours=48):
        candidato += timedelta(days=7)
    return candidato


@pytest.fixture
def operatore(martedi_prossimo):
    user = User.objects.create_user(email='op-api@example.com', password='x')
    op = Operatore.objects.create(user=user, nome='Operatore API')
    Disponibilita.objects.create(
        operatore=op,
        giorno_settimana=GiornoSettimana(martedi_prossimo.weekday()),
        ora_inizio=time(9, 0),
        ora_fine=time(18, 0),
    )
    return op


@pytest.fixture
def servizio():
    return Servizio.objects.create(
        nome='Taglio', categoria='Taglio', durata_minuti=30, prezzo='20.00'
    )


class TestSlotDisponibili:
    def test_endpoint_restituisce_slot(
        self, api_client, cliente_utente, operatore, servizio, martedi_prossimo
    ):
        response = api_client.get(
            '/api/v1/slot-disponibili/',
            {
                'operatore': str(operatore.id),
                'servizio': str(servizio.id),
                'data': martedi_prossimo.isoformat(),
            },
        )
        assert response.status_code == 200
        assert len(response.data) > 0
        assert 'inizio' in response.data[0] and 'fine' in response.data[0]

    def test_parametri_mancanti_400(self, api_client, cliente_utente):
        response = api_client.get('/api/v1/slot-disponibili/')
        assert response.status_code == 400


class TestCreazionePrenotazione:
    def test_cliente_prenota_per_se_stesso(
        self, api_client, cliente_utente, operatore, servizio, martedi_prossimo
    ):
        response = api_client.post(
            '/api/v1/prenotazioni/',
            {
                'operatore': str(operatore.id),
                'servizio': str(servizio.id),
                'inizio': _dt(martedi_prossimo, time(10, 0)).isoformat(),
            },
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 201, response.data
        prenotazione = Prenotazione.objects.get(id=response.data['id'])
        assert prenotazione.cliente.user == cliente_utente
        assert prenotazione.fine == prenotazione.inizio + timedelta(minutes=30)

    def test_cliente_non_puo_prenotare_per_un_altro_cliente(
        self, api_client, cliente_utente, operatore, servizio, martedi_prossimo
    ):
        # Creato come dato puro (niente fixture *_utente aggiuntiva): usare
        # due fixture che fanno login sullo stesso client condiviso farebbe
        # si' che la seconda sovrascriva la sessione della prima.
        altro_cliente = Cliente.objects.create(nome='Altro', email='altro-cli@example.com')

        response = api_client.post(
            '/api/v1/prenotazioni/',
            {
                'cliente': str(altro_cliente.id),
                'operatore': str(operatore.id),
                'servizio': str(servizio.id),
                'inizio': _dt(martedi_prossimo, time(10, 0)).isoformat(),
            },
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 201
        # il cliente specificato nella richiesta viene ignorato: si prenota per se' stessi
        prenotazione = Prenotazione.objects.get(id=response.data['id'])
        assert prenotazione.cliente.user == cliente_utente

    def test_slot_gia_occupato_rifiutato_a_livello_applicativo(
        self, api_client, cliente_utente, operatore, servizio, martedi_prossimo
    ):
        orario = _dt(martedi_prossimo, time(10, 0))
        api_client.post(
            '/api/v1/prenotazioni/',
            {
                'operatore': str(operatore.id),
                'servizio': str(servizio.id),
                'inizio': orario.isoformat(),
            },
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )

        response = api_client.post(
            '/api/v1/prenotazioni/',
            {
                'operatore': str(operatore.id),
                'servizio': str(servizio.id),
                'inizio': orario.isoformat(),
            },
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 400
        assert 'inizio' in response.data

    def test_staff_deve_specificare_il_cliente(
        self, api_client, admin_utente, operatore, servizio, martedi_prossimo
    ):
        response = api_client.post(
            '/api/v1/prenotazioni/',
            {
                'operatore': str(operatore.id),
                'servizio': str(servizio.id),
                'inizio': _dt(martedi_prossimo, time(10, 0)).isoformat(),
            },
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 400
        assert 'cliente' in response.data


class TestVincoloDatabase:
    """Verifica che il vincolo di esclusione Postgres blocchi l'overlap
    ANCHE bypassando completamente la validazione applicativa (simula una
    race condition: due richieste concorrenti che superano entrambe la
    validazione Python prima che una delle due arrivi a scrivere sul DB)."""

    def test_exclusion_constraint_blocca_overlap_anche_via_orm_diretto(
        self, operatore, servizio, martedi_prossimo
    ):
        cliente1 = Cliente.objects.create(nome='Race 1', email='race1@example.com')
        cliente2 = Cliente.objects.create(nome='Race 2', email='race2@example.com')

        inizio = _dt(martedi_prossimo, time(14, 0))
        fine = inizio + timedelta(minutes=30)

        Prenotazione.objects.create(
            cliente=cliente1, operatore=operatore, servizio=servizio, inizio=inizio, fine=fine
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            Prenotazione.objects.create(
                cliente=cliente2, operatore=operatore, servizio=servizio, inizio=inizio, fine=fine
            )

    def test_vincolo_db_ignora_prenotazioni_cancellate(self, operatore, servizio, martedi_prossimo):
        cliente = Cliente.objects.create(nome='Cliente', email='cancellata@example.com')
        inizio = _dt(martedi_prossimo, time(15, 0))
        fine = inizio + timedelta(minutes=30)

        Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=inizio,
            fine=fine,
            stato=StatoPrenotazione.CANCELLATA,
        )
        # stesso slot esatto, ma la prima e' cancellata: non deve sollevare IntegrityError
        Prenotazione.objects.create(
            cliente=cliente, operatore=operatore, servizio=servizio, inizio=inizio, fine=fine
        )


class TestScopingPrenotazioni:
    def test_operatore_vede_solo_le_proprie_prenotazioni(
        self, api_client, operatore_utente, servizio, martedi_prossimo
    ):
        altro_operatore_user = User.objects.create_user(email='altro-op@example.com', password='x')
        altro_operatore = Operatore.objects.create(
            user=altro_operatore_user, nome='Altro Operatore'
        )
        cliente = Cliente.objects.create(nome='Cliente Scope', email='cli-scope@example.com')

        Prenotazione.objects.create(
            cliente=cliente,
            operatore=altro_operatore,
            servizio=servizio,
            inizio=_dt(martedi_prossimo, time(11, 0)),
            fine=_dt(martedi_prossimo, time(11, 30)),
        )

        response = api_client.get('/api/v1/prenotazioni/')
        assert response.status_code == 200
        # operatore_utente non ha un profilo Operatore proprio in questo test:
        # non deve vedere la prenotazione di un altro operatore.
        assert response.data['count'] == 0

    def test_cliente_vede_solo_le_proprie(
        self, api_client, cliente_utente, operatore, servizio, martedi_prossimo
    ):
        Prenotazione.objects.create(
            cliente=cliente_utente.cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=_dt(martedi_prossimo, time(9, 0)),
            fine=_dt(martedi_prossimo, time(9, 30)),
        )
        altro_cliente = Cliente.objects.create(nome='Altro', email='altro-scope@example.com')
        Prenotazione.objects.create(
            cliente=altro_cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=_dt(martedi_prossimo, time(11, 0)),
            fine=_dt(martedi_prossimo, time(11, 30)),
        )

        response = api_client.get('/api/v1/prenotazioni/')
        assert response.status_code == 200
        assert response.data['count'] == 1


class TestCancellazione:
    def test_cliente_cancella_con_ampio_preavviso(
        self, api_client, cliente_utente, operatore, servizio, martedi_prossimo
    ):
        create_response = api_client.post(
            '/api/v1/prenotazioni/',
            {
                'operatore': str(operatore.id),
                'servizio': str(servizio.id),
                'inizio': _dt(martedi_prossimo, time(10, 0)).isoformat(),
            },
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        prenotazione_id = create_response.data['id']

        response = api_client.post(
            f'/api/v1/prenotazioni/{prenotazione_id}/cancella/',
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 200
        assert response.data['stato'] == StatoPrenotazione.CANCELLATA

    def test_cliente_non_cancella_fuori_dai_termini(
        self, api_client, cliente_utente, operatore, servizio
    ):
        prenotazione = Prenotazione.objects.create(
            cliente=cliente_utente.cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=timezone.now() + timedelta(hours=1),
            fine=timezone.now() + timedelta(hours=1, minutes=30),
        )

        response = api_client.post(
            f'/api/v1/prenotazioni/{prenotazione.id}/cancella/',
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 400
        prenotazione.refresh_from_db()
        assert prenotazione.stato == StatoPrenotazione.CONFERMATA

    def test_amministratore_cancella_anche_fuori_dai_termini(
        self, api_client, admin_utente, operatore, servizio
    ):
        # Cliente creato come dato puro, non tramite la fixture cliente_utente:
        # qui l'attore che agisce (login sul client condiviso) e' solo admin_utente.
        cliente = Cliente.objects.create(
            nome='Cliente Admin Canc', email='cli-admin-canc@example.com'
        )
        prenotazione = Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=timezone.now() + timedelta(hours=1),
            fine=timezone.now() + timedelta(hours=1, minutes=30),
        )

        response = api_client.post(
            f'/api/v1/prenotazioni/{prenotazione.id}/cancella/',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200


class TestModificaSenzaRipianificazione:
    """Regressione trovata in fase di revisione: modificare solo la nota non
    deve fallire anche se l'operatore collegato viene disattivato nel
    frattempo (vedi serializers.PrenotazioneSerializer.validate)."""

    def test_modifica_solo_nota_con_operatore_nel_frattempo_disattivato(
        self, api_client, admin_utente, operatore, servizio
    ):
        cliente = Cliente.objects.create(nome='Cliente Nota', email='cli-nota@example.com')
        prenotazione = Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=timezone.now() + timedelta(days=2),
            fine=timezone.now() + timedelta(days=2, minutes=30),
        )
        operatore.attivo = False
        operatore.save(update_fields=['attivo'])

        response = api_client.patch(
            f'/api/v1/prenotazioni/{prenotazione.id}/',
            {'note': 'Il cliente ha chiesto di arrivare 5 minuti prima'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200, response.data
