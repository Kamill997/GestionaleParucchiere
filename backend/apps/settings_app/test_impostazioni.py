import pytest

from .models import DEFAULTS, Impostazione, get_int

pytestmark = pytest.mark.django_db


class TestListaImpostazioni:
    def test_amministratore_vede_tutte_le_chiavi_note(self, api_client, admin_utente):
        response = api_client.get('/api/v1/impostazioni/')
        assert response.status_code == 200
        chiavi = {riga['chiave'] for riga in response.data['results']}
        assert chiavi == set(DEFAULTS.keys())

    def test_lista_crea_pigramente_le_chiavi_mai_toccate(self, api_client, admin_utente):
        assert not Impostazione.objects.filter(chiave='soglia_no_show').exists()
        response = api_client.get('/api/v1/impostazioni/')
        assert response.status_code == 200
        assert Impostazione.objects.filter(chiave='soglia_no_show').exists()

    def test_operatore_non_accede(self, api_client, operatore_utente):
        response = api_client.get('/api/v1/impostazioni/')
        assert response.status_code == 403

    def test_cliente_non_accede(self, api_client, cliente_utente):
        response = api_client.get('/api/v1/impostazioni/')
        assert response.status_code == 403


class TestModificaImpostazione:
    def test_amministratore_aggiorna_valore(self, api_client, admin_utente):
        impostazione = Impostazione.objects.create(
            chiave='soglia_no_show', valore='3', descrizione=DEFAULTS['soglia_no_show'][1]
        )
        response = api_client.patch(
            f'/api/v1/impostazioni/{impostazione.id}/',
            {'valore': '5'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200, response.data
        impostazione.refresh_from_db()
        assert impostazione.valore == '5'
        assert get_int('soglia_no_show') == 5

    def test_valore_non_numerico_rifiutato(self, api_client, admin_utente):
        impostazione = Impostazione.objects.create(
            chiave='soglia_no_show', valore='3', descrizione=DEFAULTS['soglia_no_show'][1]
        )
        response = api_client.patch(
            f'/api/v1/impostazioni/{impostazione.id}/',
            {'valore': 'non-un-numero'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 400
        impostazione.refresh_from_db()
        assert impostazione.valore == '3'

    def test_valore_negativo_rifiutato(self, api_client, admin_utente):
        impostazione = Impostazione.objects.create(
            chiave='buffer_minuti_prenotazioni',
            valore='10',
            descrizione=DEFAULTS['buffer_minuti_prenotazioni'][1],
        )
        response = api_client.patch(
            f'/api/v1/impostazioni/{impostazione.id}/',
            {'valore': '-5'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 400

    def test_chiave_non_modificabile(self, api_client, admin_utente):
        impostazione = Impostazione.objects.create(
            chiave='soglia_no_show', valore='3', descrizione=DEFAULTS['soglia_no_show'][1]
        )
        response = api_client.patch(
            f'/api/v1/impostazioni/{impostazione.id}/',
            {'chiave': 'chiave_inventata', 'valore': '4'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200
        impostazione.refresh_from_db()
        assert impostazione.chiave == 'soglia_no_show'

    def test_operatore_non_puo_modificare(self, api_client, operatore_utente):
        impostazione = Impostazione.objects.create(
            chiave='soglia_no_show', valore='3', descrizione=DEFAULTS['soglia_no_show'][1]
        )
        response = api_client.patch(
            f'/api/v1/impostazioni/{impostazione.id}/',
            {'valore': '10'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=operatore_utente.csrf_token,
        )
        assert response.status_code == 403
