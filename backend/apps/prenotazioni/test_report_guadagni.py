from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.clienti.models import Cliente
from apps.operatori.models import Operatore
from apps.servizi.models import Servizio
from apps.settings_app.models import Impostazione
from apps.users.models import User

from .models import Prenotazione, StatoPagamento
from .services import calcola_report_guadagni

pytestmark = pytest.mark.django_db


@pytest.fixture
def scenario_guadagni():
    oggi = timezone.localdate()
    op_user = User.objects.create_user(email='op-report@example.com', password='x')
    operatore = Operatore.objects.create(user=op_user, nome='Operatore Report')
    cliente_top = Cliente.objects.create(nome='Cliente Top', email='cliente-top@example.com')
    cliente_basso = Cliente.objects.create(nome='Cliente Basso', email='cliente-basso@example.com')
    taglio = Servizio.objects.create(
        nome='Taglio', categoria='Taglio', durata_minuti=30, prezzo='20.00'
    )
    colore = Servizio.objects.create(
        nome='Colore', categoria='Colore', durata_minuti=60, prezzo='50.00'
    )

    inizio = timezone.make_aware(timezone.datetime.combine(oggi, time(10, 0)))
    Prenotazione.objects.create(
        cliente=cliente_top,
        operatore=operatore,
        servizio=colore,
        inizio=inizio,
        fine=inizio + timedelta(minutes=60),
        stato_pagamento=StatoPagamento.PAGATO,
        importo='50.00',
    )
    Prenotazione.objects.create(
        cliente=cliente_basso,
        operatore=operatore,
        servizio=taglio,
        inizio=inizio + timedelta(hours=2),
        fine=inizio + timedelta(hours=2, minutes=30),
        stato_pagamento=StatoPagamento.PAGATO,
        importo='20.00',
    )
    # non pagata: non deve contare in nessuna delle viste
    Prenotazione.objects.create(
        cliente=cliente_basso,
        operatore=operatore,
        servizio=taglio,
        inizio=inizio + timedelta(hours=4),
        fine=inizio + timedelta(hours=4, minutes=30),
        stato_pagamento=StatoPagamento.NON_PAGATO,
    )
    return {'cliente_top': cliente_top, 'cliente_basso': cliente_basso, 'operatore': operatore}


class TestReportGuadagni:
    def test_per_servizio_somma_solo_le_pagate(self, scenario_guadagni):
        report = calcola_report_guadagni()
        per_servizio = {riga['nome']: riga['totale'] for riga in report['per_servizio']}
        assert per_servizio['Colore'] == '50.00'
        assert per_servizio['Taglio'] == '20.00'  # non conta la seconda, non pagata

    def test_per_operatore_somma_tutte_le_pagate(self, scenario_guadagni):
        report = calcola_report_guadagni()
        assert len(report['per_operatore']) == 1
        assert report['per_operatore'][0]['totale'] == '70.00'

    def test_top_clienti_ordinato_per_totale_decrescente(self, scenario_guadagni):
        report = calcola_report_guadagni()
        nomi = [riga['nome'] for riga in report['top_clienti']]
        assert nomi[0] == 'Cliente Top'  # 50.00 > 20.00
        assert nomi[1] == 'Cliente Basso'

    def test_clienti_vicini_al_blocco(self, scenario_guadagni):
        Impostazione.objects.update_or_create(chiave='soglia_no_show', defaults={'valore': '3'})
        scenario_guadagni['cliente_basso'].contatore_no_show = 2  # soglia(3) - 1
        scenario_guadagni['cliente_basso'].save(update_fields=['contatore_no_show'])

        report = calcola_report_guadagni()

        nomi_vicini = [riga['nome'] for riga in report['clienti_vicini_al_blocco']]
        assert 'Cliente Basso' in nomi_vicini
        assert 'Cliente Top' not in nomi_vicini

    def test_cliente_gia_bloccato_non_compare_tra_i_vicini(self, scenario_guadagni):
        """Un cliente gia' bloccato non e' 'vicino' alla soglia: ci e'
        gia' arrivato (vedi services.segna_presenza)."""
        Impostazione.objects.update_or_create(chiave='soglia_no_show', defaults={'valore': '3'})
        scenario_guadagni['cliente_basso'].contatore_no_show = 3
        scenario_guadagni['cliente_basso'].bloccato = True
        scenario_guadagni['cliente_basso'].save(update_fields=['contatore_no_show', 'bloccato'])

        report = calcola_report_guadagni()

        nomi_vicini = [riga['nome'] for riga in report['clienti_vicini_al_blocco']]
        assert 'Cliente Basso' not in nomi_vicini

    def test_nessun_dato_non_esplode(self):
        report = calcola_report_guadagni()
        assert report == {
            'per_servizio': [],
            'per_operatore': [],
            'top_clienti': [],
            'clienti_vicini_al_blocco': [],
        }


class TestEndpointReportGuadagni:
    def test_amministratore_accede(self, api_client, admin_utente, scenario_guadagni):
        response = api_client.get('/api/v1/dashboard/report-guadagni/')
        assert response.status_code == 200
        assert 'per_servizio' in response.data
        assert 'top_clienti' in response.data

    def test_operatore_non_accede(self, api_client, operatore_utente):
        """A differenza del KPI generale, il report guadagni e' riservato
        esplicitamente ad Amministratore (docs/08-pagamenti.md: "Dashboard
        guadagni (lato Amministratore)")."""
        response = api_client.get('/api/v1/dashboard/report-guadagni/')
        assert response.status_code == 403

    def test_cliente_non_accede(self, api_client, cliente_utente):
        response = api_client.get('/api/v1/dashboard/report-guadagni/')
        assert response.status_code == 403
