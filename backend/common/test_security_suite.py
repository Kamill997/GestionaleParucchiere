import io
from PIL import Image
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError

from common.middleware import ContentSecurityPolicyMiddleware
from common.throttling import LoginRateThrottle
from common.validators import validate_image_upload, validate_document_upload


def _crea_immagine_in_memoria(formato='JPEG', size=(50, 50), color=(255, 0, 0)):
    buffer = io.BytesIO()
    img = Image.new('RGB', size, color)
    img.save(buffer, format=formato)
    return buffer.getvalue()


class TestValidazioneMimeUpload:
    """Verifica sicurezza upload file (MIME type, magic bytes e integrità Pillow)."""

    def test_upload_immagine_valida_jpeg(self):
        data = _crea_immagine_in_memoria('JPEG')
        f = SimpleUploadedFile('foto.jpg', data, content_type='image/jpeg')
        risultato = validate_image_upload(f)
        assert risultato is f

    def test_upload_immagine_valida_png(self):
        data = _crea_immagine_in_memoria('PNG')
        f = SimpleUploadedFile('foto.png', data, content_type='image/png')
        risultato = validate_image_upload(f)
        assert risultato is f

    def test_upload_immagine_valida_webp(self):
        data = _crea_immagine_in_memoria('WEBP')
        f = SimpleUploadedFile('foto.webp', data, content_type='image/webp')
        risultato = validate_image_upload(f)
        assert risultato is f

    def test_upload_falso_jpeg_con_script_o_binario_rifiutato(self):
        # File nominato .jpg ma contenente script HTML
        fake_content = b'<html><script>alert("xss")</script></html>'
        f = SimpleUploadedFile('fake.jpg', fake_content, content_type='image/jpeg')
        with pytest.raises(ValidationError) as exc:
            validate_image_upload(f)
        assert 'non corrisponde a una firma immagine valida' in str(exc.value)

    def test_upload_estensione_non_permessa(self):
        data = _crea_immagine_in_memoria('JPEG')
        f = SimpleUploadedFile('documento.pdf', data, content_type='application/pdf')
        with pytest.raises(ValidationError) as exc:
            validate_image_upload(f)
        assert 'Formato immagine non supportato' in str(exc.value)

    def test_upload_immagine_supera_dimensione_massima(self):
        # Crea immagine fittizia che supera 1 MB quando il limite è 1 MB
        data = b'\xff\xd8\xff' + b'0' * (2 * 1024 * 1024)
        f = SimpleUploadedFile('pesante.jpg', data, content_type='image/jpeg')
        with pytest.raises(ValidationError) as exc:
            validate_image_upload(f, max_size_mb=1)
        assert 'La dimensione della foto non può superare' in str(exc.value)

    def test_upload_csv_valido(self):
        csv_data = b'Nome,Email,Telefono\nMario Rossi,mario@test.it,+393331234567\n'
        f = SimpleUploadedFile('clienti.csv', csv_data, content_type='text/csv')
        risultato = validate_document_upload(f)
        assert risultato is f

    def test_upload_csv_con_payload_binario_pericoloso_rifiutato(self):
        # File nominato .csv ma con magic bytes MZ di un eseguibile Windows
        malicious_data = b'MZ\x90\x00\x03\x00\x00\x00' + b'dummy content'
        f = SimpleUploadedFile('clienti.csv', malicious_data, content_type='text/csv')
        with pytest.raises(ValidationError) as exc:
            validate_document_upload(f)
        assert 'intestazioni binarie o script non consentiti' in str(exc.value)


class TestContentSecurityPolicyMiddleware:
    """Verifica che il middleware inietti gli header OWASP e CSP su tutte le risposte."""

    def test_csp_header_presenti(self):
        factory = RequestFactory()
        request = factory.get('/')
        middleware = ContentSecurityPolicyMiddleware(lambda req: HttpResponse('OK'))
        response = middleware(request)

        assert 'Content-Security-Policy' in response
        csp = response['Content-Security-Policy']
        assert "default-src 'self'" in csp
        assert "object-src 'none'" in csp
        assert "frame-ancestors 'none'" in csp

        # Header aggiuntivi
        assert response['X-Content-Type-Options'] == 'nosniff'
        assert response['Referrer-Policy'] == 'strict-origin-when-cross-origin'
        assert 'geolocation=()' in response['Permissions-Policy']


class TestThrottlingSicurezza:
    """Verifica la risoluzione corretta dell'IP reale in presenza di reverse proxy."""

    def test_estrazione_ip_reale_da_x_forwarded_for(self):
        factory = RequestFactory()
        request = factory.get('/api/v1/auth/login/', HTTP_X_FORWARDED_FOR='203.0.113.195, 10.0.0.1')
        throttle = LoginRateThrottle()
        ip = throttle.get_ident(request)
        assert ip == '203.0.113.195'

    def test_fallback_su_remote_addr_senza_proxy(self):
        factory = RequestFactory()
        request = factory.get('/api/v1/auth/login/', REMOTE_ADDR='198.51.100.22')
        throttle = LoginRateThrottle()
        ip = throttle.get_ident(request)
        assert ip == '198.51.100.22'
