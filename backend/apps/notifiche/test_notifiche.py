import pytest
from django.core import mail

from apps.clienti.models import Cliente
from apps.roles.models import Role
from apps.users.models import User

from .models import Notifica, TipoNotifica
from .services import crea_notifica, notifica_amministratori, notifica_cliente

pytestmark = pytest.mark.django_db


class TestCreaNotifica:
    def test_crea_notifica_in_app_e_invia_email_per_tipi_con_email(self):
        utente = User.objects.create_user(email='dest@example.com', password='x')

        crea_notifica(utente, TipoNotifica.CONFERMA_PRENOTAZIONE, 'Titolo', 'Messaggio')

        assert Notifica.objects.filter(destinatario=utente, tipo='conferma_prenotazione').exists()
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['dest@example.com']
        assert mail.outbox[0].subject == 'Titolo'

    def test_crea_notifica_niente_email_per_tipi_solo_in_app(self):
        """docs/esempio-settore-parrucchiere.md: "Nuova prenotazione
        ricevuta" e' "in-app, eventualmente push", non email."""
        utente = User.objects.create_user(email='operatore@example.com', password='x')

        crea_notifica(utente, TipoNotifica.NUOVA_PRENOTAZIONE_RICEVUTA, 'Titolo', 'Messaggio')

        assert Notifica.objects.filter(destinatario=utente).exists()
        assert len(mail.outbox) == 0


class TestNotificaCliente:
    def test_cliente_registrato_riceve_in_app_e_email(self):
        utente = User.objects.create_user(email='cliente@example.com', password='x')
        cliente = Cliente.objects.create(user=utente, nome='Cliente Reg', email=utente.email)

        notifica_cliente(cliente, TipoNotifica.CONFERMA_PRENOTAZIONE, 'Titolo', 'Messaggio')

        assert Notifica.objects.filter(destinatario=utente).exists()
        assert len(mail.outbox) == 1

    def test_cliente_ospite_riceve_solo_email_diretta(self):
        """docs/08-pagamenti.md: il conteggio no-show funziona "anche per
        prenotazioni senza account" - le notifiche devono coprire lo stesso
        caso: niente riga Notifica (nessuno User a cui agganciarla), solo
        email diretta all'indirizzo del Cliente."""
        cliente_ospite = Cliente.objects.create(nome='Ospite', email='ospite@example.com')

        risultato = notifica_cliente(
            cliente_ospite, TipoNotifica.CONFERMA_PRENOTAZIONE, 'Titolo', 'Messaggio'
        )

        assert risultato is None
        assert Notifica.objects.count() == 0
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ['ospite@example.com']

    def test_cliente_ospite_senza_email_non_esplode(self):
        cliente_ospite = Cliente.objects.create(nome='Ospite Senza Email')
        notifica_cliente(cliente_ospite, TipoNotifica.CONFERMA_PRENOTAZIONE, 'Titolo', 'Messaggio')
        assert len(mail.outbox) == 0


class TestNotificaAmministratori:
    def test_notifica_tutti_gli_amministratori(self):
        ruolo, _ = Role.objects.get_or_create(nome='Amministratore')
        admin1 = User.objects.create_user(email='admin1@example.com', password='x')
        admin1.roles.add(ruolo)
        admin2 = User.objects.create_user(email='admin2@example.com', password='x')
        admin2.roles.add(ruolo)
        User.objects.create_user(email='non-admin@example.com', password='x')  # non deve ricevere

        notifiche = notifica_amministratori(TipoNotifica.CLIENTE_BLOCCATO, 'Titolo', 'Messaggio')

        assert len(notifiche) == 2
        assert Notifica.objects.filter(destinatario=admin1).exists()
        assert Notifica.objects.filter(destinatario=admin2).exists()
        assert not Notifica.objects.filter(destinatario__email='non-admin@example.com').exists()


class TestAPINotifiche:
    def test_utente_vede_solo_le_proprie_notifiche(self, api_client, cliente_utente):
        Notifica.objects.create(
            destinatario=cliente_utente, tipo='conferma_prenotazione', titolo='Mia', messaggio='x'
        )
        altro = User.objects.create_user(email='altro-notifiche@example.com', password='x')
        Notifica.objects.create(
            destinatario=altro, tipo='conferma_prenotazione', titolo='Non mia', messaggio='x'
        )

        response = api_client.get('/api/v1/notifiche/')

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['titolo'] == 'Mia'

    def test_conteggio_non_lette(self, api_client, cliente_utente):
        Notifica.objects.create(
            destinatario=cliente_utente, tipo='conferma_prenotazione', titolo='A', messaggio='x'
        )
        Notifica.objects.create(
            destinatario=cliente_utente,
            tipo='conferma_prenotazione',
            titolo='B',
            messaggio='x',
            letta=True,
        )

        response = api_client.get('/api/v1/notifiche/non-lette-count/')

        assert response.status_code == 200
        assert response.data['conteggio'] == 1

    def test_segna_letta(self, api_client, cliente_utente):
        notifica = Notifica.objects.create(
            destinatario=cliente_utente, tipo='conferma_prenotazione', titolo='A', messaggio='x'
        )

        response = api_client.post(
            f'/api/v1/notifiche/{notifica.id}/segna-letta/',
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )

        assert response.status_code == 200
        notifica.refresh_from_db()
        assert notifica.letta is True

    def test_segna_tutte_lette(self, api_client, cliente_utente):
        Notifica.objects.create(
            destinatario=cliente_utente, tipo='conferma_prenotazione', titolo='A', messaggio='x'
        )
        Notifica.objects.create(
            destinatario=cliente_utente, tipo='conferma_prenotazione', titolo='B', messaggio='x'
        )

        response = api_client.post(
            '/api/v1/notifiche/segna-tutte-lette/', HTTP_X_CSRFTOKEN=cliente_utente.csrf_token
        )

        assert response.status_code == 200
        assert response.data['aggiornate'] == 2
        assert Notifica.objects.filter(destinatario=cliente_utente, letta=False).count() == 0

    def test_utente_non_puo_segnare_letta_una_notifica_altrui(self, api_client, cliente_utente):
        altro = User.objects.create_user(email='altro-letta@example.com', password='x')
        notifica_altrui = Notifica.objects.create(
            destinatario=altro, tipo='conferma_prenotazione', titolo='A', messaggio='x'
        )

        response = api_client.post(
            f'/api/v1/notifiche/{notifica_altrui.id}/segna-letta/',
            HTTP_X_CSRFTOKEN=cliente_utente.csrf_token,
        )

        assert response.status_code == 404  # fuori dal proprio queryset
