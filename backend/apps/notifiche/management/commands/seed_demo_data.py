"""management command: python manage.py seed_demo_data

Crea un set minimo di dati di esempio per verificare che il deploy sia
andato a buon fine (login, catalogo, notifiche). NON eseguire su un
ambiente gia' in produzione con dati reali: il comando e' idempotente
(get_or_create) ma potrebbe sovrascrivere valori esistenti.

Uso consigliato: subito dopo il primo deploy, prima di consegnare il
sistema al cliente.
"""

from django.core.management.base import BaseCommand

ADMIN_EMAIL = 'admin@demo.local'
ADMIN_PASSWORD = 'demo-password-sicura-123'
CLIENTE_EMAIL = 'cliente@demo.local'
CLIENTE_PASSWORD = 'demo-password-sicura-123'


class Command(BaseCommand):
    help = 'Crea dati di esempio per verificare il primo deploy'

    def handle(self, *args, **options):
        from apps.clienti.models import Cliente
        from apps.operatori.models import Disponibilita, GiornoSettimana, Operatore
        from apps.roles.models import Role
        from apps.servizi.models import Servizio
        from apps.settings_app.models import Impostazione
        from apps.users.models import User

        self.stdout.write('Creazione ruoli...')
        admin_role, _ = Role.objects.get_or_create(nome='Amministratore')
        op_role, _ = Role.objects.get_or_create(nome='Operatore')
        cliente_role, _ = Role.objects.get_or_create(nome='Cliente')

        self.stdout.write('Creazione utente amministratore...')
        admin, created = User.objects.get_or_create(email=ADMIN_EMAIL)
        if created or not admin.check_password(ADMIN_PASSWORD):
            admin.set_password(ADMIN_PASSWORD)
            admin.first_name = 'Admin'
            admin.is_staff = True
            admin.save()
        admin.roles.set([admin_role])
        if created:
            self.stdout.write(f'  Admin creato: {ADMIN_EMAIL} / {ADMIN_PASSWORD}')
        else:
            self.stdout.write(f"  Admin gia' esistente: {ADMIN_EMAIL}")

        self.stdout.write('Creazione utente operatore...')
        op_user, _ = User.objects.get_or_create(email='giulia@demo.local')
        op_user.set_password(ADMIN_PASSWORD)
        op_user.first_name = 'Giulia'
        op_user.last_name = 'Bianchi'
        op_user.save()
        op_user.roles.set([op_role])
        operatore, _ = Operatore.objects.get_or_create(
            user=op_user, defaults={'nome': 'Giulia Bianchi', 'specializzazioni': 'Taglio, Colore'}
        )
        # Disponibilita' lun-sab 9-18
        for giorno in [0, 1, 2, 3, 4, 5]:  # lun-sab
            from datetime import time

            Disponibilita.objects.get_or_create(
                operatore=operatore,
                giorno_settimana=GiornoSettimana(giorno),
                defaults={'ora_inizio': time(9, 0), 'ora_fine': time(18, 0)},
            )

        self.stdout.write('Creazione utente cliente...')
        cli_user, created = User.objects.get_or_create(email=CLIENTE_EMAIL)
        if created or not cli_user.check_password(CLIENTE_PASSWORD):
            cli_user.set_password(CLIENTE_PASSWORD)
            cli_user.first_name = 'Mario'
            cli_user.last_name = 'Rossi'
            cli_user.save()
        cli_user.roles.set([cliente_role])
        Cliente.objects.get_or_create(
            user=cli_user,
            defaults={'nome': 'Mario Rossi', 'email': CLIENTE_EMAIL, 'telefono': '3331234567'},
        )
        if created:
            self.stdout.write(f'  Cliente creato: {CLIENTE_EMAIL} / {CLIENTE_PASSWORD}')

        self.stdout.write('Creazione catalogo servizi...')
        catalogo = [
            ('Taglio uomo', 'Taglio', 30, '18.00'),
            ('Taglio donna', 'Taglio', 45, '28.00'),
            ('Colore base', 'Colore', 60, '45.00'),
            ('Colore + taglio', 'Colore', 90, '65.00'),
            ('Trattamento cheratina', 'Trattamento', 120, '85.00'),
            ('Barba', 'Barba', 20, '12.00'),
        ]
        for nome, categoria, durata, prezzo in catalogo:
            Servizio.objects.get_or_create(
                nome=nome,
                defaults={
                    'categoria': categoria,
                    'durata_minuti': durata,
                    'prezzo': prezzo,
                    'attivo': True,
                },
            )

        self.stdout.write('Impostazioni di default...')
        defaults = {
            'buffer_minuti_prenotazioni': '10',
            'intervallo_slot_minuti': '15',
            'ore_preavviso_cancellazione': '24',
            'soglia_no_show': '3',
        }
        for chiave, valore in defaults.items():
            Impostazione.objects.get_or_create(chiave=chiave, defaults={'valore': valore})

        self.stdout.write(self.style.SUCCESS('\nDati demo pronti!'))
        self.stdout.write(f'  Admin:   {ADMIN_EMAIL} / {ADMIN_PASSWORD}')
        self.stdout.write(f'  Cliente: {CLIENTE_EMAIL} / {CLIENTE_PASSWORD}')
        self.stdout.write('  URL backend: http://localhost:8000/')
        self.stdout.write('  Django Admin: http://localhost:8000/admin/')
