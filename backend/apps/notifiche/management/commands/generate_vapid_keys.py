"""management command: python manage.py generate_vapid_keys

Genera una coppia di chiavi VAPID e stampa i valori da copiare in .env.
Eseguire una volta sola prima del primo deploy: cambiare le chiavi dopo
invalida tutte le sottoscrizioni push esistenti.
Vedi docs/04-pwa-checklist.md, "Notifiche push"."""

import base64

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Genera una coppia di chiavi VAPID per le notifiche push PWA'

    def handle(self, *args, **options):
        try:
            from cryptography.hazmat.primitives.serialization import (
                Encoding,
                PublicFormat,
            )
            from py_vapid import Vapid
        except ImportError:
            self.stderr.write('Installa pywebpush e cryptography: pip install pywebpush')
            return

        vapid = Vapid()
        vapid.generate_keys()

        private_pem = vapid.private_pem().decode().strip()
        public_bytes = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')

        self.stdout.write('\nAggiungi queste righe al tuo file .env:\n')
        self.stdout.write(f'VAPID_PRIVATE_KEY={private_pem}')
        self.stdout.write(f'VAPID_PUBLIC_KEY={public_key_b64}')
        self.stdout.write('\nATTENZIONE: non cambiare le chiavi dopo il deploy.')
