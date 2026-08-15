import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.audit_log.models import AuditLog

from .models import Cliente

pytestmark = pytest.mark.django_db


def _csv(righe: list[str]) -> bytes:
    intestazione = 'nome,email,telefono,note_preferenze'
    return '\n'.join([intestazione, *righe]).encode('utf-8')


def _upload(contenuto: bytes, nome='clienti.csv', content_type='text/csv'):
    return SimpleUploadedFile(nome, contenuto, content_type=content_type)


class TestTemplateImport:
    def test_amministratore_scarica_il_template(self, api_client, admin_utente):
        response = api_client.get('/api/v1/clienti/template-import/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
        contenuto = response.content.decode('utf-8')
        assert contenuto.splitlines()[0] == 'nome,email,telefono,note_preferenze'
        assert len(contenuto.splitlines()) == 2  # intestazione + riga di esempio

    def test_operatore_non_puo_scaricare_il_template(self, api_client, operatore_utente):
        response = api_client.get('/api/v1/clienti/template-import/')
        assert response.status_code == 403

    def test_cliente_non_puo_scaricare_il_template(self, api_client, cliente_utente):
        response = api_client.get('/api/v1/clienti/template-import/')
        assert response.status_code == 403


class TestImportazione:
    def test_crea_clienti_da_righe_valide(self, api_client, admin_utente):
        contenuto = _csv(
            [
                'Mario Rossi,mario@example.com,3331112222,Colore castano',
                'Anna Verdi,anna@example.com,3339998888,',
            ]
        )
        response = api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(contenuto)},
            format='multipart',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200, response.data
        assert response.data['creati'] == 2
        assert response.data['aggiornati'] == 0
        assert response.data['errori'] == []
        assert Cliente.objects.filter(email='mario@example.com', nome='Mario Rossi').exists()
        assert Cliente.objects.filter(email='anna@example.com').exists()

    def test_aggiorna_cliente_esistente_invece_di_duplicarlo(self, api_client, admin_utente):
        esistente = Cliente.objects.create(
            nome='Vecchio Nome', email='gia-presente@example.com', telefono='000'
        )
        contenuto = _csv(['Nome Aggiornato,gia-presente@example.com,3330001111,Nota nuova'])

        response = api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(contenuto)},
            format='multipart',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )

        assert response.status_code == 200, response.data
        assert response.data['creati'] == 0
        assert response.data['aggiornati'] == 1
        assert Cliente.objects.filter(email='gia-presente@example.com').count() == 1
        esistente.refresh_from_db()
        assert esistente.nome == 'Nome Aggiornato'
        assert esistente.telefono == '3330001111'

    def test_riga_senza_nome_obbligatorio_finisce_negli_errori_altre_righe_ok(
        self, api_client, admin_utente
    ):
        contenuto = _csv(
            [
                ',senza-nome@example.com,123,',
                'Cliente Ok,ok@example.com,456,',
            ]
        )
        response = api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(contenuto)},
            format='multipart',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200, response.data
        assert response.data['creati'] == 1
        assert len(response.data['errori']) == 1
        assert response.data['errori'][0]['riga'] == 2  # riga 1 e' l'header
        assert Cliente.objects.filter(email='ok@example.com').exists()
        assert not Cliente.objects.filter(email='senza-nome@example.com').exists()

    def test_email_duplicata_nel_file_segnalata_nel_report(self, api_client, admin_utente):
        contenuto = _csv(
            [
                'Primo,duplicata@example.com,111,',
                'Secondo (stessa email),duplicata@example.com,222,',
            ]
        )
        response = api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(contenuto)},
            format='multipart',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200, response.data
        assert len(response.data['duplicati_interni']) == 1
        assert response.data['duplicati_interni'][0]['email'] == 'duplicata@example.com'
        # la seconda riga aggiorna il cliente appena creato dalla prima, non lo duplica
        assert Cliente.objects.filter(email='duplicata@example.com').count() == 1
        assert Cliente.objects.get(email='duplicata@example.com').nome == 'Secondo (stessa email)'

    def test_estensione_non_supportata_rifiutata(self, api_client, admin_utente):
        response = api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(b'contenuto', nome='clienti.txt', content_type='text/plain')},
            format='multipart',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 400
        assert Cliente.objects.count() == 0

    def test_file_oltre_5mb_rifiutato(self, api_client, admin_utente):
        contenuto_grande = b'a' * (5 * 1024 * 1024 + 1)
        response = api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(contenuto_grande)},
            format='multipart',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 400

    def test_colonne_mancanti_restituisce_errore_chiaro_invece_di_500(
        self, api_client, admin_utente
    ):
        contenuto = b'nome,email\nMario,mario@example.com'
        response = api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(contenuto)},
            format='multipart',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 200
        assert response.data['creati'] == 0
        assert 'Colonne mancanti' in response.data['errori'][0]['messaggio']

    def test_file_non_leggibile_restituisce_400_non_500(self, api_client, admin_utente):
        response = api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(b'\x00\x01binario-non-csv', nome='clienti.xlsx')},
            format='multipart',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        assert response.status_code == 400

    def test_operatore_non_puo_importare(self, api_client, operatore_utente):
        response = api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(_csv(['Mario,mario@example.com,123,']))},
            format='multipart',
            HTTP_X_CSRFTOKEN=operatore_utente.csrf_token,
        )
        assert response.status_code == 403

    def test_import_registra_evento_in_audit_log(self, api_client, admin_utente):
        api_client.post(
            '/api/v1/clienti/importa/',
            {'file': _upload(_csv(['Mario,mario@example.com,123,']))},
            format='multipart',
            HTTP_X_CSRFTOKEN=admin_utente.csrf_token,
        )
        log = AuditLog.objects.get(azione='clienti_importati')
        assert log.user == admin_utente
        assert log.dettagli['creati'] == 1


class TestEsportazione:
    def test_amministratore_esporta_csv(self, api_client, admin_utente):
        Cliente.objects.create(nome='Cliente Export', email='export@example.com', telefono='999')

        response = api_client.get('/api/v1/clienti/esporta/')

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
        contenuto = response.content.decode('utf-8')
        assert 'export@example.com' in contenuto
        assert contenuto.splitlines()[0] == 'nome,email,telefono,note_preferenze'

    def test_esportazione_rispetta_la_ricerca_attiva(self, api_client, admin_utente):
        Cliente.objects.create(nome='Trovami', email='trovami@example.com')
        Cliente.objects.create(nome='Altro Cliente', email='altro-export@example.com')

        response = api_client.get('/api/v1/clienti/esporta/', {'search': 'Trovami'})

        contenuto = response.content.decode('utf-8')
        assert 'trovami@example.com' in contenuto
        assert 'altro-export@example.com' not in contenuto

    def test_operatore_non_puo_esportare(self, api_client, operatore_utente):
        response = api_client.get('/api/v1/clienti/esporta/')
        assert response.status_code == 403

    def test_cliente_non_puo_esportare(self, api_client, cliente_utente):
        response = api_client.get('/api/v1/clienti/esporta/')
        assert response.status_code == 403

    def test_esportazione_registra_evento_in_audit_log(self, api_client, admin_utente):
        Cliente.objects.create(nome='Per Audit', email='per-audit@example.com')
        api_client.get('/api/v1/clienti/esporta/')
        log = AuditLog.objects.get(azione='clienti_esportati')
        assert log.user == admin_utente
