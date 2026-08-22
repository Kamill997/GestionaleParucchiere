from datetime import date, datetime, time, timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.clienti.models import Cliente
from apps.notifiche.models import Notifica
from apps.operatori.models import Disponibilita, GiornoSettimana, Operatore
from apps.roles.models import Role
from apps.servizi.models import Servizio
from apps.users.models import User

from .models import Prenotazione
from .services import segna_presenza
from .tasks import invia_promemoria_prenotazioni

pytestmark = pytest.mark.django_db


def _dt(giorno: date, ora: time):
    return timezone.make_aware(datetime.combine(giorno, ora))


@pytest.fixture
def martedi_prossimo():
    ora = timezone.now()
    giorni_al_martedi = (1 - ora.weekday()) % 7 or 7
    candidato = ora.date() + timedelta(days=giorni_al_martedi)
    inizio_candidato = timezone.make_aware(datetime.combine(candidato, time(10, 0)))
    if inizio_candidato - ora < timedelta(hours=48):
        candidato += timedelta(days=7)
    return candidato


@pytest.fixture
def operatore(martedi_prossimo):
    user = User.objects.create_user(email='op-notif@example.com', password='x')
    op = Operatore.objects.create(user=user, nome='Operatore Notifiche')
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


class TestNotifichePrenotazione:
    def test_creazione_notifica_cliente_e_operatore(
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

        assert Notifica.objects.filter(
            destinatario=cliente_utente, tipo='conferma_prenotazione'
        ).exists()
        assert Notifica.objects.filter(
            destinatario=operatore.user, tipo='nuova_prenotazione_ricevuta'
        ).exists()
        # solo la conferma al cliente genera email, non la notifica interna all'operatore
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [cliente_utente.email]

    def test_cancellazione_da_staff_notifica_il_cliente(
        self, api_client, admin_utente, operatore, servizio
    ):
        cliente_user = User.objects.create_user(email='cli-canc-notif@example.com', password='x')
        cliente = Cliente.objects.create(
            user=cliente_user, nome='Cliente', email=cliente_user.email
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
        assert Notifica.objects.filter(
            destinatario=cliente_user, tipo='cancellazione_prenotazione'
        ).exists()

    def test_cancellazione_da_cliente_non_notifica_se_stesso(
        self, api_client, cliente_utente, operatore, servizio, martedi_prossimo
    ):
        create_response = api_client.post(
            '/api/v1/prenotazioni/',
            {
                'operatore': str(operatore.id),
                'servizio': str(servizio.id),
                'inizio': _dt(martedi_prossimo, time(11, 0)).isoformat(),
            },
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )
        # pulisco la notifica di conferma appena creata: non e' quella sotto esame qui
        Notifica.objects.all().delete()
        mail.outbox.clear()

        response = api_client.post(
            f'/api/v1/prenotazioni/{create_response.data["id"]}/cancella/',
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )

        assert response.status_code == 200
        assert not Notifica.objects.filter(tipo='cancellazione_prenotazione').exists()
        assert len(mail.outbox) == 0


class TestNotificheNoShow:
    def test_soglia_raggiunta_notifica_cliente_ed_amministratori(self):
        ruolo, _ = Role.objects.get_or_create(nome='Amministratore')
        admin = User.objects.create_user(email='admin-notif@example.com', password='x')
        admin.roles.add(ruolo)

        op_user = User.objects.create_user(email='op-soglia@example.com', password='x')
        operatore = Operatore.objects.create(user=op_user, nome='Op Soglia')
        cliente_user = User.objects.create_user(email='cli-soglia@example.com', password='x')
        cliente = Cliente.objects.create(
            user=cliente_user,
            nome='Cliente Soglia',
            email=cliente_user.email,
            contatore_no_show=2,  # a un passo dalla soglia default (3)
        )
        servizio = Servizio.objects.create(
            nome='Taglio', categoria='Taglio', durata_minuti=30, prezzo='20.00'
        )
        inizio = timezone.now() - timedelta(days=1)
        prenotazione = Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=inizio,
            fine=inizio + timedelta(minutes=30),
        )

        segna_presenza(prenotazione, 'non_presente')

        assert Notifica.objects.filter(
            destinatario=cliente_user, tipo='soglia_no_show_raggiunta'
        ).exists()
        assert Notifica.objects.filter(destinatario=admin, tipo='cliente_bloccato').exists()
        assert len(mail.outbox) == 1  # solo il cliente riceve email per questo tipo


class TestPromemoriaTask:
    def test_invia_promemoria_solo_per_prenotazioni_nella_finestra(
        self, operatore, servizio, martedi_prossimo
    ):
        cliente_user = User.objects.create_user(email='cli-promemoria@example.com', password='x')
        cliente = Cliente.objects.create(
            user=cliente_user, nome='Cliente Promemoria', email=cliente_user.email
        )

        # dentro la finestra 24h-24h15m da adesso
        inizio_domani = timezone.now() + timedelta(hours=24, minutes=5)
        prenotazione_domani = Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=inizio_domani,
            fine=inizio_domani + timedelta(minutes=30),
        )
        # fuori dalla finestra (fra 3 giorni)
        inizio_lontano = timezone.now() + timedelta(days=3)
        Prenotazione.objects.create(
            cliente=cliente,
            operatore=operatore,
            servizio=servizio,
            inizio=inizio_lontano,
            fine=inizio_lontano + timedelta(minutes=30),
        )

        inviati = invia_promemoria_prenotazioni()

        assert inviati == 1
        notifica = Notifica.objects.get(destinatario=cliente_user, tipo='promemoria_prenotazione')
        assert str(prenotazione_domani.servizio.nome) in notifica.messaggio
