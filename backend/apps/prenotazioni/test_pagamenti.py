from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.audit_log.models import AuditLog
from apps.clienti.models import Cliente
from apps.operatori.models import Disponibilita, GiornoSettimana, Operatore
from apps.servizi.models import Servizio
from apps.settings_app.models import Impostazione
from apps.users.models import User

from .models import Prenotazione, StatoPagamento, StatoPresenza
from .services import sblocca_cliente, segna_presenza

pytestmark = pytest.mark.django_db


@pytest.fixture
def prenotazione_passata():
    """Una prenotazione nel passato: la marcatura presenza si applica ad
    appuntamenti gia' avvenuti."""
    op_user = User.objects.create_user(email='op-presenza@example.com', password='x')
    operatore = Operatore.objects.create(user=op_user, nome='Op Presenza')
    cliente = Cliente.objects.create(nome='Cliente Presenza', email='cli-presenza@example.com')
    servizio = Servizio.objects.create(
        nome='Taglio', categoria='Taglio', durata_minuti=30, prezzo='25.00'
    )
    inizio = timezone.now() - timedelta(days=1)
    return Prenotazione.objects.create(
        cliente=cliente,
        operatore=operatore,
        servizio=servizio,
        inizio=inizio,
        fine=inizio + timedelta(minutes=30),
    )


class TestImportoDefault:
    def test_importo_preso_dal_servizio_se_non_specificato(self, prenotazione_passata):
        assert prenotazione_passata.importo == prenotazione_passata.servizio.prezzo

    def test_importo_esplicito_non_sovrascritto(self):
        op_user = User.objects.create_user(email='op-sconto@example.com', password='x')
        operatore = Operatore.objects.create(user=op_user, nome='Op Sconto')
        cliente = Cliente.objects.create(nome='Cliente Sconto', email='cli-sconto@example.com')
        servizio = Servizio.objects.create(
            nome='Colore', categoria='Colore', durata_minuti=60, prezzo='50.00'
        )
        inizio = timezone.now() + timedelta(days=1)
        prenotazione = Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=inizio,
            fine=inizio + timedelta(minutes=60),
            importo='35.00',
        )
        assert str(prenotazione.importo) == '35.00'


class TestSegnaPresenza:
    def test_presente_non_incrementa_il_contatore(self, prenotazione_passata):
        segna_presenza(prenotazione_passata, StatoPresenza.PRESENTE)
        prenotazione_passata.cliente.refresh_from_db()
        assert prenotazione_passata.cliente.contatore_no_show == 0

    def test_non_presente_incrementa_il_contatore(self, prenotazione_passata):
        segna_presenza(prenotazione_passata, StatoPresenza.NON_PRESENTE)
        prenotazione_passata.cliente.refresh_from_db()
        assert prenotazione_passata.cliente.contatore_no_show == 1
        assert prenotazione_passata.cliente.bloccato is False  # sotto soglia (default 3)

    def test_blocco_automatico_al_raggiungimento_della_soglia(self, prenotazione_passata):
        Impostazione.objects.update_or_create(chiave='soglia_no_show', defaults={'valore': '2'})
        cliente = prenotazione_passata.cliente
        operatore = prenotazione_passata.operatore
        servizio = prenotazione_passata.servizio

        segna_presenza(prenotazione_passata, StatoPresenza.NON_PRESENTE)
        cliente.refresh_from_db()
        assert cliente.bloccato is False  # 1 su soglia 2

        inizio2 = timezone.now() - timedelta(days=2)
        seconda = Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=inizio2,
            fine=inizio2 + timedelta(minutes=30),
        )
        admin_user = User.objects.create_user(email='admin-blocco@example.com', password='x')
        segna_presenza(seconda, StatoPresenza.NON_PRESENTE, autore=admin_user)

        cliente.refresh_from_db()
        assert cliente.contatore_no_show == 2
        assert cliente.bloccato is True
        log = AuditLog.objects.get(azione='cliente_bloccato_no_show')
        assert log.user == admin_user
        assert log.dettagli['contatore_no_show'] == 2

    def test_ripetere_non_presente_non_incrementa_due_volte(self, prenotazione_passata):
        segna_presenza(prenotazione_passata, StatoPresenza.NON_PRESENTE)
        segna_presenza(prenotazione_passata, StatoPresenza.NON_PRESENTE)  # stesso stato, ripetuto
        prenotazione_passata.cliente.refresh_from_db()
        assert prenotazione_passata.cliente.contatore_no_show == 1


class TestSbloccaCliente:
    def test_sblocca_rimuove_il_blocco_ma_non_il_contatore(self):
        cliente = Cliente.objects.create(
            nome='Cliente Bloccato',
            email='cli-bloccato@example.com',
            bloccato=True,
            contatore_no_show=3,
        )
        admin_user = User.objects.create_user(email='admin-sblocca@example.com', password='x')

        sblocca_cliente(cliente, autore=admin_user)

        cliente.refresh_from_db()
        assert cliente.bloccato is False
        assert cliente.contatore_no_show == 3  # storico, non azzerato
        assert AuditLog.objects.filter(azione='cliente_sbloccato').exists()

    def test_sblocca_su_cliente_gia_sbloccato_non_crea_log(self):
        cliente = Cliente.objects.create(nome='Cliente Ok', email='cli-ok@example.com')
        sblocca_cliente(cliente)
        assert not AuditLog.objects.filter(azione='cliente_sbloccato').exists()


class TestAPISegnaPresenza:
    def test_cliente_non_puo_segnare_presenza(
        self, api_client, cliente_utente, prenotazione_passata
    ):
        response = api_client.post(
            f'/api/v1/prenotazioni/{prenotazione_passata.id}/segna-presenza/',
            {'stato_presenza': 'presente'},
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 403

    def test_operatore_puo_segnare_presenza_per_una_propria_prenotazione(
        self, api_client, operatore_utente
    ):
        # get_queryset scopa un Operatore alle sole prenotazioni assegnate a
        # se stesso: serve un profilo Operatore collegato proprio a
        # operatore_utente, non una prenotazione di un operatore qualsiasi
        # (la fixture prenotazione_passata usa un operatore indipendente).
        mio_operatore = Operatore.objects.create(user=operatore_utente, nome='Operatore Del Test')
        cliente = Cliente.objects.create(nome='Cliente Del Test', email='cli-del-test@example.com')
        servizio = Servizio.objects.create(
            nome='Taglio', categoria='Taglio', durata_minuti=30, prezzo='20.00'
        )
        inizio = timezone.now() - timedelta(days=1)
        prenotazione = Prenotazione.objects.create(
            cliente=cliente,
            operatore=mio_operatore,
            servizio=servizio,
            inizio=inizio,
            fine=inizio + timedelta(minutes=30),
        )

        response = api_client.post(
            f'/api/v1/prenotazioni/{prenotazione.id}/segna-presenza/',
            {'stato_presenza': 'non_presente'},
            HTTP_X_CSRFTOKEN=operatore_utente.csrf_token,
        )
        assert response.status_code == 200, response.data
        prenotazione.refresh_from_db()
        assert prenotazione.stato_presenza == StatoPresenza.NON_PRESENTE


class TestAPISblocco:
    def test_operatore_non_puo_sbloccare(self, api_client, operatore_utente):
        cliente = Cliente.objects.create(nome='X', email='x-sblocco@example.com', bloccato=True)
        response = api_client.post(
            f'/api/v1/clienti/{cliente.id}/sblocca/', HTTP_X_CSRFTOKEN=operatore_utente.csrf_token
        )
        assert response.status_code == 403

    def test_amministratore_puo_sbloccare(self, api_client, admin_utente):
        cliente = Cliente.objects.create(nome='Y', email='y-sblocco@example.com', bloccato=True)
        response = api_client.post(
            f'/api/v1/clienti/{cliente.id}/sblocca/', HTTP_X_CSRFTOKEN=admin_utente.csrf_token
        )
        assert response.status_code == 200
        cliente.refresh_from_db()
        assert cliente.bloccato is False


class TestClienteBloccatoNonPrenota:
    def test_cliente_bloccato_non_puo_creare_prenotazioni(self, api_client, cliente_utente):
        cliente_utente.cliente.bloccato = True
        cliente_utente.cliente.save(update_fields=['bloccato'])

        op_user = User.objects.create_user(email='op-blocco-prenota@example.com', password='x')
        operatore = Operatore.objects.create(user=op_user, nome='Op Blocco')
        oggi = timezone.localdate()
        Disponibilita.objects.create(
            operatore=operatore,
            giorno_settimana=GiornoSettimana(oggi.weekday()),
            ora_inizio=time(0, 0),
            ora_fine=time(23, 59),
        )
        servizio = Servizio.objects.create(
            nome='Taglio', categoria='Taglio', durata_minuti=30, prezzo='20.00'
        )
        inizio = timezone.now() + timedelta(hours=1)

        response = api_client.post(
            '/api/v1/prenotazioni/',
            {
                'operatore': str(operatore.id),
                'servizio': str(servizio.id),
                'inizio': inizio.isoformat(),
            },
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        assert response.status_code == 400


class TestPagamentoStaffOnly:
    def test_cliente_non_puo_segnarsi_come_pagato(
        self, api_client, cliente_utente, prenotazione_passata
    ):
        # prenotazione_passata non e' del cliente_utente, ma basta arrivare
        # alla validazione del campo per verificare il blocco (403 di scope
        # arriverebbe comunque prima per altri motivi su un altro cliente,
        # quindi qui si usa direttamente il serializer per isolare la regola).
        from .serializers import PrenotazioneSerializer

        class FakeRequest:
            user = cliente_utente

        serializer = PrenotazioneSerializer(
            prenotazione_passata,
            data={'stato_pagamento': 'pagato'},
            partial=True,
            context={'request': FakeRequest()},
        )
        assert serializer.is_valid() is False
        assert 'non_field_errors' in serializer.errors or serializer.errors

    def test_staff_puo_segnare_pagato(self, api_client, admin_utente, prenotazione_passata):
        response = api_client.patch(
            f'/api/v1/prenotazioni/{prenotazione_passata.id}/',
            {'stato_pagamento': 'pagato'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200, response.data
        prenotazione_passata.refresh_from_db()
        assert prenotazione_passata.stato_pagamento == StatoPagamento.PAGATO


class TestKPIConPagamenti:
    def test_fatturato_e_tasso_no_show_nel_payload(self, api_client, admin_utente):
        response = api_client.get('/api/v1/dashboard/kpi/')
        assert response.status_code == 200
        assert 'fatturato_settimana' in response.data
        assert 'tasso_no_show' in response.data
