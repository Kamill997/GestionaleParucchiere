from datetime import time, timedelta

import pytest
from django.utils import timezone

from apps.clienti.models import Cliente
from apps.operatori.models import Disponibilita, GiornoSettimana, Operatore
from apps.servizi.models import Servizio
from apps.users.models import User

from .models import Prenotazione, StatoPrenotazione
from .services import calcola_kpi_dashboard

pytestmark = pytest.mark.django_db


@pytest.fixture
def scenario_kpi():
    oggi = timezone.localdate()
    user = User.objects.create_user(email='op-kpi@example.com', password='x')
    operatore = Operatore.objects.create(user=user, nome='Op KPI')
    Disponibilita.objects.create(
        operatore=operatore,
        giorno_settimana=GiornoSettimana(oggi.weekday()),
        ora_inizio=time(9, 0),
        ora_fine=time(13, 0),  # 240 minuti disponibili oggi
    )
    cliente = Cliente.objects.create(nome='Cliente KPI', email='cli-kpi@example.com')
    servizio = Servizio.objects.create(
        nome='Taglio', categoria='Taglio', durata_minuti=30, prezzo='20.00'
    )

    inizio_oggi = timezone.make_aware(timezone.datetime.combine(oggi, time(9, 0)))
    Prenotazione.objects.create(
        cliente=cliente,
        operatore=operatore,
        servizio=servizio,
        inizio=inizio_oggi,
        fine=inizio_oggi + timedelta(minutes=30),
    )
    # una seconda prenotazione oggi, stesso servizio, cosi' e' anche il piu' richiesto
    Prenotazione.objects.create(
        cliente=cliente,
        operatore=operatore,
        servizio=servizio,
        inizio=inizio_oggi + timedelta(hours=2),
        fine=inizio_oggi + timedelta(hours=2, minutes=30),
    )
    # una cancellata: non deve contare
    Prenotazione.objects.create(
        cliente=cliente,
        operatore=operatore,
        servizio=servizio,
        inizio=inizio_oggi + timedelta(hours=3),
        fine=inizio_oggi + timedelta(hours=3, minutes=30),
        stato=StatoPrenotazione.CANCELLATA,
    )
    return {'operatore': operatore, 'cliente': cliente, 'servizio': servizio, 'oggi': oggi}


class TestCalcoloKPI:
    def test_conta_solo_prenotazioni_attive_di_oggi(self, scenario_kpi):
        kpi = calcola_kpi_dashboard(scenario_kpi['oggi'])
        assert kpi['prenotazioni_oggi'] == 2  # non la cancellata

    def test_servizio_piu_richiesto(self, scenario_kpi):
        kpi = calcola_kpi_dashboard(scenario_kpi['oggi'])
        assert kpi['servizio_piu_richiesto'] == {'nome': 'Taglio', 'conteggio': 2}

    def test_tasso_occupazione(self, scenario_kpi):
        kpi = calcola_kpi_dashboard(scenario_kpi['oggi'])
        # 240 minuti disponibili (9-13), 60 minuti prenotati (2x30) -> 25%
        assert kpi['tasso_occupazione_oggi'] == 25.0

    def test_nessun_dato_non_esplode(self):
        kpi = calcola_kpi_dashboard(timezone.localdate())
        assert kpi['prenotazioni_oggi'] == 0
        assert kpi['servizio_piu_richiesto'] is None
        assert kpi['tasso_occupazione_oggi'] == 0.0


class TestEndpointKPI:
    def test_cliente_non_accede_ai_kpi(self, api_client, cliente_utente):
        response = api_client.get('/api/v1/dashboard/kpi/')
        assert response.status_code == 403

    def test_amministratore_accede_ai_kpi(self, api_client, admin_utente, scenario_kpi):
        response = api_client.get('/api/v1/dashboard/kpi/')
        assert response.status_code == 200
        assert response.data['prenotazioni_oggi'] == 2

    def test_operatore_accede_ai_kpi(self, api_client, operatore_utente, scenario_kpi):
        response = api_client.get('/api/v1/dashboard/kpi/')
        assert response.status_code == 200
