from datetime import date, datetime, time

import pytest
from django.utils import timezone

from apps.clienti.models import Cliente
from apps.operatori.models import Disponibilita, GiornoSettimana, Operatore
from apps.prenotazioni.models import Prenotazione, StatoPrenotazione
from apps.prenotazioni.services import calcola_slot_liberi, puo_cancellare_liberamente
from apps.servizi.models import Servizio
from apps.users.models import User

pytestmark = pytest.mark.django_db


def _dt(giorno: date, ora: time):
    return timezone.make_aware(datetime.combine(giorno, ora))


@pytest.fixture
def martedi():
    # 2026-01-06 e' un martedi' (weekday()==1); usato come giorno fisso di test.
    return date(2026, 1, 6)


@pytest.fixture
def operatore_con_turno(martedi):
    user = User.objects.create_user(email='op-slot@example.com', password='x')
    operatore = Operatore.objects.create(user=user, nome='Op Test')
    Disponibilita.objects.create(
        operatore=operatore,
        giorno_settimana=GiornoSettimana.MARTEDI,
        ora_inizio=time(9, 0),
        ora_fine=time(11, 0),
    )
    return operatore


@pytest.fixture
def servizio_30min():
    return Servizio.objects.create(
        nome='Taglio', categoria='Taglio', durata_minuti=30, prezzo='20.00'
    )


class TestCalcolaSlotLiberi:
    def test_turno_vuoto_offre_slot_ogni_15_minuti(
        self, operatore_con_turno, servizio_30min, martedi
    ):
        slot = calcola_slot_liberi(operatore_con_turno, servizio_30min, martedi)
        # turno 09:00-11:00, servizio 30 min, passo 15 min -> ultimo slot valido inizia alle 10:30
        assert slot[0] == (_dt(martedi, time(9, 0)), _dt(martedi, time(9, 30)))
        assert slot[-1] == (_dt(martedi, time(10, 30)), _dt(martedi, time(11, 0)))
        assert len(slot) == 7  # 09:00, 09:15, 09:30, 09:45, 10:00, 10:15, 10:30

    def test_giorno_senza_turno_nessuno_slot(self, operatore_con_turno, servizio_30min):
        mercoledi = date(2026, 1, 7)
        assert calcola_slot_liberi(operatore_con_turno, servizio_30min, mercoledi) == []

    def test_prenotazione_esistente_blocca_lo_slot_e_il_buffer(
        self, operatore_con_turno, servizio_30min, martedi
    ):
        cliente_user = User.objects.create_user(email='cli-slot@example.com', password='x')
        cliente = Cliente.objects.create(user=cliente_user, nome='Cliente Test')
        Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore_con_turno,
            servizio=servizio_30min,
            inizio=_dt(martedi, time(9, 30)),
            fine=_dt(martedi, time(10, 0)),
        )

        slot = calcola_slot_liberi(operatore_con_turno, servizio_30min, martedi)
        orari_inizio = [s[0].time() for s in slot]

        # 09:00 (fine 09:30) e' adiacente esatto alla prenotazione (09:30-10:00),
        # ma il buffer di 10 minuti lo esclude comunque.
        assert time(9, 0) not in orari_inizio
        assert time(9, 15) not in orari_inizio
        # la prenotazione stessa e i suoi dintorni non devono comparire
        assert time(9, 30) not in orari_inizio
        assert time(9, 45) not in orari_inizio
        # 10:10 (con buffer, fine occupazione 10:00+10min=10:10) e' il primo slot libero,
        # ma il passo e' di 15 min a partire da 09:00 -> il primo multiplo disponibile e' 10:15
        assert time(10, 15) in orari_inizio

    def test_prenotazione_cancellata_non_blocca_lo_slot(
        self, operatore_con_turno, servizio_30min, martedi
    ):
        cliente_user = User.objects.create_user(email='cli-slot2@example.com', password='x')
        cliente = Cliente.objects.create(user=cliente_user, nome='Cliente Test 2')
        Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore_con_turno,
            servizio=servizio_30min,
            inizio=_dt(martedi, time(9, 30)),
            fine=_dt(martedi, time(10, 0)),
            stato=StatoPrenotazione.CANCELLATA,
        )

        slot = calcola_slot_liberi(operatore_con_turno, servizio_30min, martedi)
        assert time(9, 30) in [s[0].time() for s in slot]


class TestPolicyCancellazione:
    def test_cancellabile_liberamente_se_ampio_preavviso(self, operatore_con_turno, servizio_30min):
        cliente_user = User.objects.create_user(email='cli-canc@example.com', password='x')
        cliente = Cliente.objects.create(user=cliente_user, nome='Cliente Canc')
        prenotazione = Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore_con_turno,
            servizio=servizio_30min,
            inizio=timezone.now() + timezone.timedelta(days=3),
            fine=timezone.now() + timezone.timedelta(days=3, minutes=30),
        )
        assert puo_cancellare_liberamente(prenotazione) is True

    def test_non_cancellabile_liberamente_sotto_soglia(self, operatore_con_turno, servizio_30min):
        cliente_user = User.objects.create_user(email='cli-canc2@example.com', password='x')
        cliente = Cliente.objects.create(user=cliente_user, nome='Cliente Canc 2')
        prenotazione = Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore_con_turno,
            servizio=servizio_30min,
            inizio=timezone.now() + timezone.timedelta(hours=2),
            fine=timezone.now() + timezone.timedelta(hours=2, minutes=30),
        )
        assert puo_cancellare_liberamente(prenotazione) is False
