"""Validatori di sicurezza per file upload (immagini e documenti).

Garantisce che i file caricati rispettino dimensioni massime, MIME type
dichiarati e firme binarie (magic bytes) reali, prevenendo attacchi
di spoofing dell'estensione o iniezione di eseguibili/script.
"""

from io import BytesIO
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

ALLOWED_IMAGE_MIMES = {'image/jpeg', 'image/png', 'image/webp'}
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}

# Firme binarie standard
MAGIC_JPEG = b'\xff\xd8\xff'
MAGIC_PNG = b'\x89PNG\r\n\x1a\n'
MAGIC_RIFF = b'RIFF'
MAGIC_WEBP = b'WEBP'
MAGIC_ZIP_XLSX = b'PK\x03\x04'

# Firme binarie pericolose vietate nei file testuali (es. CSV)
DANGEROUS_BINARY_HEADERS = (
    b'MZ',          # Eseguibile Windows PE (.exe, .dll)
    b'\x7fELF',     # Eseguibile Linux ELF
    b'PK\x03\x04',  # Archivio ZIP
    b'\x1f\x8b',    # Gzip
    b'<!DOCTYPE',   # HTML / XML / SVG potenzialmente con script
    b'<html',
    b'<script',
)


def validate_image_upload(file, max_size_mb: int = 5):
    """Valida un file immagine caricato (dimensione, MIME type, magic bytes e integrita' Pillow)."""
    if not file:
        return file

    # 1. Dimensione massima
    max_bytes = max_size_mb * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f'La dimensione della foto non può superare {max_size_mb} MB.')

    # 2. Content-Type dichiarato
    content_type = getattr(file, 'content_type', '').lower()
    if content_type and content_type not in ALLOWED_IMAGE_MIMES:
        raise ValidationError(
            f'Formato immagine non supportato ({content_type}). Sono consentiti solo JPEG, PNG e WebP.'
        )

    # 3. Magic bytes
    try:
        file.seek(0)
        header = file.read(16)
        file.seek(0)
    except Exception:
        raise ValidationError('Impossibile leggere il file immagine caricato.')

    is_jpeg = header.startswith(MAGIC_JPEG)
    is_png = header.startswith(MAGIC_PNG)
    is_webp = header.startswith(MAGIC_RIFF) and MAGIC_WEBP in header

    if not (is_jpeg or is_png or is_webp):
        raise ValidationError('Il file caricato non corrisponde a una firma immagine valida (JPEG, PNG o WebP).')

    # 4. Decodifica effettiva con Pillow
    try:
        file.seek(0)
        data = file.read()
        file.seek(0)
        with Image.open(BytesIO(data)) as img:
            img.verify()
            if img.format not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError(f'Formato immagine ({img.format}) non ammesso.')
    except (UnidentifiedImageError, SyntaxError, ValidationError):
        raise ValidationError('Il file caricato non è un\'immagine valida o è danneggiato.')
    except Exception:
        raise ValidationError('Errore durante la validazione dell\'immagine.')

    return file


def validate_document_upload(file, max_size_mb: int = 5):
    """Valida un documento di import (CSV o XLSX)."""
    if not file:
        raise ValidationError('Nessun file fornito.')

    nome = getattr(file, 'name', '').lower()
    max_bytes = max_size_mb * 1024 * 1024

    if file.size > max_bytes:
        raise ValidationError(f'Il file supera la dimensione massima consentita di {max_size_mb} MB.')

    if not (nome.endswith('.csv') or nome.endswith('.xlsx')):
        raise ValidationError('Formato non supportato. Sono ammessi solo file .csv e .xlsx.')

    try:
        file.seek(0)
        header = file.read(64)
        file.seek(0)
    except Exception:
        raise ValidationError('Impossibile leggere il file caricato.')

    if nome.endswith('.xlsx'):
        if not header.startswith(MAGIC_ZIP_XLSX):
            raise ValidationError('Il file .xlsx caricato non è un archivio di foglio di calcolo valido.')
    elif nome.endswith('.csv'):
        for bad_header in DANGEROUS_BINARY_HEADERS:
            if header.startswith(bad_header):
                raise ValidationError('Il file .csv caricato contiene intestazioni binarie o script non consentiti.')
        # Verifica che non contenga byte nulli tipici di file binari
        if b'\x00' in header:
            raise ValidationError('Il file .csv contiene caratteri binari non validi.')

    return file
