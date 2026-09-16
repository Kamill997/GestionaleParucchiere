"""management command: python manage.py populate_db

Popola il database con dati realistici di un salone per consentire di
provare tutte le funzionalita' dell'app senza doverle creare a mano:

  - 1 Amministratore + 3 Operatrici + 8 Clienti registrati + 7 ospiti
  - 10 servizi del catalogo (Taglio, Colore, Trattamento, Barba)
  - ~80 prenotazioni distribuite tra -3 mesi e +1 mese da oggi
    (passate completate/pagate, passate no-show, future confermate)
  - Notifiche di esempio gia' lette/non lette
  - Impostazioni realistiche del salone

ATTENZIONE: esegui SOLO su un DB di sviluppo/staging. Il comando non
cancella i dati esistenti ma e' idempotente per email/chiavi univoche.

Uso:
  python manage.py populate_db
  python manage.py populate_db --pulisci   # azzera prima il DB
"""

import random
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

# ---------------------------------------------------------------------------
# Dati di esempio
# ---------------------------------------------------------------------------

OPERATRICI = [
    {
        'email': 'giulia@salone.demo',
        'nome': 'Giulia',
        'cognome': 'Bianchi',
        'operatore_nome': 'Giulia Bianchi',
        'specializzazioni': 'Taglio donna, Colore, Trattamenti',
    },
    {
        'email': 'sara@salone.demo',
        'nome': 'Sara',
        'cognome': 'Conti',
        'operatore_nome': 'Sara Conti',
        'specializzazioni': 'Taglio uomo, Barba, Sfumature',
    },
    {
        'email': 'marta@salone.demo',
        'nome': 'Marta',
        'cognome': 'Esposito',
        'operatore_nome': 'Marta Esposito',
        'specializzazioni': 'Colorazione balayage, Meches, Trattamenti cheratina',
    },
]

CLIENTI_REGISTRATI = [
    {'email': 'mario.rossi@demo.it', 'nome': 'Mario', 'cognome': 'Rossi', 'tel': '3331001001'},
    {'email': 'lucia.ferrari@demo.it', 'nome': 'Lucia', 'cognome': 'Ferrari', 'tel': '3332002002'},
    {'email': 'anna.romano@demo.it', 'nome': 'Anna', 'cognome': 'Romano', 'tel': '3333003003'},
    {
        'email': 'giuseppe.ricci@demo.it',
        'nome': 'Giuseppe',
        'cognome': 'Ricci',
        'tel': '3334004004',
    },
    {'email': 'elena.marino@demo.it', 'nome': 'Elena', 'cognome': 'Marino', 'tel': '3335005005'},
    {'email': 'luca.greco@demo.it', 'nome': 'Luca', 'cognome': 'Greco', 'tel': '3336006006'},
    {
        'email': 'chiara.lombardi@demo.it',
        'nome': 'Chiara',
        'cognome': 'Lombardi',
        'tel': '3337007007',
    },
    {'email': 'marco.gallo@demo.it', 'nome': 'Marco', 'cognome': 'Gallo', 'tel': '3338008008'},
]

CLIENTI_OSPITI = [
    {'nome': 'Francesca Bruno', 'email': 'f.bruno@demo.it', 'tel': '3339009001'},
    {'nome': 'Davide Coppola', 'email': 'd.coppola@demo.it', 'tel': '3339009002'},
    {'nome': 'Silvia De Luca', 'email': 's.deluca@demo.it', 'tel': '3339009003'},
    {'nome': 'Alberto Ferrara', 'email': 'a.ferrara@demo.it', 'tel': '3339009004'},
    {'nome': 'Roberta Gentile', 'email': 'r.gentile@demo.it', 'tel': '3339009005'},
    {'nome': 'Nicola Leone', 'email': '', 'tel': '3339009006'},
    {'nome': 'Teresa Martinelli', 'email': 't.martinelli@demo.it', 'tel': '3339009007'},
]

SERVIZI = [
    {'nome': 'Taglio uomo', 'categoria': 'Taglio', 'durata_minuti': 30, 'prezzo': '18.00'},
    {'nome': 'Taglio donna corto', 'categoria': 'Taglio', 'durata_minuti': 45, 'prezzo': '28.00'},
    {'nome': 'Taglio donna lungo', 'categoria': 'Taglio', 'durata_minuti': 60, 'prezzo': '35.00'},
    {'nome': 'Piega', 'categoria': 'Taglio', 'durata_minuti': 45, 'prezzo': '22.00'},
    {'nome': 'Colore base', 'categoria': 'Colore', 'durata_minuti': 75, 'prezzo': '55.00'},
    {'nome': 'Balayage / Meches', 'categoria': 'Colore', 'durata_minuti': 120, 'prezzo': '90.00'},
    {'nome': 'Colore + Taglio', 'categoria': 'Colore', 'durata_minuti': 100, 'prezzo': '78.00'},
    {
        'nome': 'Trattamento cheratina',
        'categoria': 'Trattamento',
        'durata_minuti': 120,
        'prezzo': '95.00',
    },
    {
        'nome': 'Trattamento rigenerante',
        'categoria': 'Trattamento',
        'durata_minuti': 45,
        'prezzo': '38.00',
    },
    {'nome': 'Barba', 'categoria': 'Barba', 'durata_minuti': 25, 'prezzo': '14.00'},
]

NOTE_CLIENTI = [
    'Preferisce non usare prodotti con ammoniaca.',
    'Capelli molto ricci, trattarli con cura.',
    'Allergia al nichel: attenzione ai fermagli.',
    'Cliente affezionata da 3 anni. Gradisce caffè durante il trattamento.',
    'Puntuale. Preferisce appuntamenti al mattino.',
    'Capelli molto fini e delicati.',
    'Vuole sempre un taglio scalato sulle punte.',
    '',
]

PASSWORD_DEMO = 'demo-password-123'


class Command(BaseCommand):
    help = 'Popola il DB con dati realistici per le prove'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pulisci',
            action='store_true',
            help='Cancella tutti i dati esistenti prima di popolare (ATTENZIONE: irreversibile)',
        )

    def handle(self, *args, **options):
        from apps.audit_log.models import AuditLog
        from apps.clienti.models import Cliente
        from apps.notifiche.models import Notifica, TipoNotifica
        from apps.operatori.models import Disponibilita, GiornoSettimana, Operatore
        from apps.prenotazioni.models import (
            Prenotazione,
            StatoPagamento,
            StatoPrenotazione,
            StatoPresenza,
        )
        from apps.roles.models import Role
        from apps.servizi.models import Servizio
        from apps.settings_app.models import Impostazione
        from apps.users.models import User

        random.seed(42)  # riproducibilita'

        if options['pulisci']:
            self.stdout.write(self.style.WARNING('Cancellazione dati esistenti...'))
            Prenotazione.objects.all().delete()
            Notifica.objects.all().delete()
            AuditLog.objects.all().delete()
            Operatore.objects.all().delete()
            Cliente.objects.filter(user__isnull=True).delete()
            Cliente.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            Servizio.objects.all().delete()

        # ------------------------------------------------------------------
        # Ruoli
        # ------------------------------------------------------------------
        self.stdout.write('Ruoli...')
        admin_role, _ = Role.objects.get_or_create(nome='Amministratore')
        op_role, _ = Role.objects.get_or_create(nome='Operatore')
        cli_role, _ = Role.objects.get_or_create(nome='Cliente')

        # ------------------------------------------------------------------
        # Admin
        # ------------------------------------------------------------------
        self.stdout.write('Amministratore...')
        admin, creato = User.objects.get_or_create(email='admin@salone.demo')
        admin.first_name = 'Titolare'
        admin.last_name = 'Salone'
        admin.is_staff = True
        admin.set_password(PASSWORD_DEMO)
        admin.save()
        admin.roles.set([admin_role])
        if creato:
            self.stdout.write(f'  ✓ admin@salone.demo / {PASSWORD_DEMO}')

        # Admin per test E2E Playwright
        admin_test, _ = User.objects.get_or_create(email='admin@test.local')
        admin_test.first_name = 'Admin'
        admin_test.last_name = 'Test'
        admin_test.is_staff = True
        admin_test.set_password('test-password-sicura-123')
        admin_test.save()
        admin_test.roles.set([admin_role])

        # ------------------------------------------------------------------
        # Impostazioni
        # ------------------------------------------------------------------
        self.stdout.write('Impostazioni...')
        impostazioni = {
            'buffer_minuti_prenotazioni': '10',
            'intervallo_slot_minuti': '15',
            'ore_preavviso_cancellazione': '24',
            'soglia_no_show': '3',
        }
        for chiave, valore in impostazioni.items():
            Impostazione.objects.update_or_create(chiave=chiave, defaults={'valore': valore})

        # ------------------------------------------------------------------
        # Servizi
        # ------------------------------------------------------------------
        self.stdout.write('Servizi...')
        servizi_db = []
        for s in SERVIZI:
            obj, _ = Servizio.objects.get_or_create(
                nome=s['nome'],
                defaults={
                    'categoria': s['categoria'],
                    'durata_minuti': s['durata_minuti'],
                    'prezzo': s['prezzo'],
                    'attivo': True,
                },
            )
            servizi_db.append(obj)
        self.stdout.write(f'  ✓ {len(servizi_db)} servizi')

        # ------------------------------------------------------------------
        # Operatrici
        # ------------------------------------------------------------------
        self.stdout.write('Operatrici...')
        operatori_db = []
        for dati in OPERATRICI:
            user, creato = User.objects.get_or_create(email=dati['email'])
            user.first_name = dati['nome']
            user.last_name = dati['cognome']
            user.set_password(PASSWORD_DEMO)
            user.save()
            user.roles.set([op_role])
            op, _ = Operatore.objects.get_or_create(
                user=user,
                defaults={
                    'nome': dati['operatore_nome'],
                    'specializzazioni': dati['specializzazioni'],
                },
            )
            # Disponibilita' lun-ven 9-19, sab 9-16
            for giorno in range(5):  # lun-ven
                Disponibilita.objects.get_or_create(
                    operatore=op,
                    giorno_settimana=GiornoSettimana(giorno),
                    defaults={'ora_inizio': time(9, 0), 'ora_fine': time(19, 0)},
                )
            Disponibilita.objects.get_or_create(
                operatore=op,
                giorno_settimana=GiornoSettimana.SABATO,
                defaults={'ora_inizio': time(9, 0), 'ora_fine': time(16, 0)},
            )
            operatori_db.append(op)
            if creato:
                self.stdout.write(f'  ✓ {dati["email"]} / {PASSWORD_DEMO}')
        self.stdout.write(f"  ✓ {len(operatori_db)} operatrici con disponibilita'")

        # ------------------------------------------------------------------
        # Clienti registrati
        # ------------------------------------------------------------------
        self.stdout.write('Clienti registrati...')
        clienti_db = []
        for i, dati in enumerate(CLIENTI_REGISTRATI):
            user, creato = User.objects.get_or_create(email=dati['email'])
            user.first_name = dati['nome']
            user.last_name = dati['cognome']
            user.set_password(PASSWORD_DEMO)
            user.save()
            user.roles.set([cli_role])
            nome_completo = f'{dati["nome"]} {dati["cognome"]}'
            cliente, _ = Cliente.objects.get_or_create(
                user=user,
                defaults={
                    'nome': nome_completo,
                    'email': dati['email'],
                    'telefono': dati['tel'],
                    'note_preferenze': NOTE_CLIENTI[i % len(NOTE_CLIENTI)],
                },
            )
            clienti_db.append(cliente)
        self.stdout.write(f'  ✓ {len(clienti_db)} clienti registrati — password: {PASSWORD_DEMO}')

        # Cliente per test E2E Playwright
        cli_test_user, _ = User.objects.get_or_create(email='cliente@test.local')
        cli_test_user.first_name = 'Cliente'
        cli_test_user.last_name = 'Test'
        cli_test_user.set_password('test-password-sicura-123')
        cli_test_user.save()
        cli_test_user.roles.set([cli_role])
        cli_test_obj, _ = Cliente.objects.get_or_create(
            user=cli_test_user,
            defaults={
                'nome': 'Cliente Test',
                'email': 'cliente@test.local',
                'telefono': '3330000000',
                'note_preferenze': 'Utente di test automatizzato Playwright',
            },
        )
        clienti_db.append(cli_test_obj)

        # ------------------------------------------------------------------
        # Clienti ospiti
        # ------------------------------------------------------------------
        self.stdout.write('Clienti ospiti...')
        for dati in CLIENTI_OSPITI:
            email = dati['email'] or ''  # il modello ha blank=True ma NOT NULL
            # Per ospiti senza email, usiamo nome come chiave di lookup
            # (get_or_create sulla combinazione nome+email vuota)
            cliente, _ = Cliente.objects.get_or_create(
                nome=dati['nome'],
                email=email,
                defaults={'telefono': dati['tel']},
            )
            clienti_db.append(cliente)
        self.stdout.write(f'  ✓ {len(CLIENTI_OSPITI)} clienti ospiti (senza account)')

        # ------------------------------------------------------------------
        # Prenotazioni (storia realistica)
        # ------------------------------------------------------------------
        self.stdout.write('Prenotazioni...')
        oggi = timezone.localdate()
        prenotazioni_create = 0

        def crea_prenotazione(
            cliente,
            operatore,
            servizio,
            giorno_offset,
            ora_inizio,
            stato=StatoPrenotazione.COMPLETATA,
            stato_pagamento=StatoPagamento.PAGATO,
            stato_presenza=StatoPresenza.PRESENTE,
            sconto=None,
        ):
            """Helper interno che salta i weekend e le collisioni orarie."""
            giorno = oggi + timedelta(days=giorno_offset)
            # Salta domenica
            if giorno.weekday() == 6:
                giorno += timedelta(days=1)
            # Salta sabato per i futuri (solo pomeriggio = poco slot)
            if giorno_offset > 0 and giorno.weekday() == 5 and ora_inizio.hour >= 16:
                return None

            tz = timezone.get_current_timezone()
            inizio_dt = timezone.make_aware(datetime.combine(giorno, ora_inizio), tz)
            fine_dt = inizio_dt + timedelta(minutes=servizio.durata_minuti)

            # Controlla collisione operatore
            collisione = (
                Prenotazione.objects.filter(
                    operatore=operatore,
                    inizio__lt=fine_dt,
                    fine__gt=inizio_dt,
                )
                .exclude(stato=StatoPrenotazione.CANCELLATA)
                .exists()
            )
            if collisione:
                return None

            importo = float(servizio.prezzo)
            if sconto:
                importo = round(importo * (1 - sconto), 2)

            try:
                pren = Prenotazione.objects.create(
                    cliente=cliente,
                    operatore=operatore,
                    servizio=servizio,
                    inizio=inizio_dt,
                    fine=fine_dt,
                    stato=stato,
                    stato_pagamento=stato_pagamento,
                    stato_presenza=stato_presenza,
                    importo=str(importo),
                )
                return pren
            except Exception:
                return None

        # --- Passato: 3 mesi di storia ---
        taglio_d = next(s for s in servizi_db if s.nome == 'Taglio donna corto')
        taglio_u = next(s for s in servizi_db if s.nome == 'Taglio uomo')
        colore = next(s for s in servizi_db if s.nome == 'Colore base')
        balayage = next(s for s in servizi_db if s.nome == 'Balayage / Meches')
        colore_taglio = next(s for s in servizi_db if s.nome == 'Colore + Taglio')
        cheratina = next(s for s in servizi_db if s.nome == 'Trattamento cheratina')
        barba = next(s for s in servizi_db if s.nome == 'Barba')
        piega = next(s for s in servizi_db if s.nome == 'Piega')
        rigenerante = next(s for s in servizi_db if s.nome == 'Trattamento rigenerante')
        taglio_lungo = next(s for s in servizi_db if s.nome == 'Taglio donna lungo')

        op0, op1, op2 = operatori_db

        # Prenotazioni passate — distribuite su 90 giorni precedenti
        storia_passata = [
            # Giulia (op0) — taglio e colore
            (-85, op0, clienti_db[0], taglio_d, time(9, 0)),
            (-80, op0, clienti_db[1], colore, time(10, 0)),
            (-78, op0, clienti_db[2], taglio_d, time(14, 0)),
            (-74, op0, clienti_db[3], colore_taglio, time(9, 0)),
            (-70, op0, clienti_db[0], balayage, time(9, 30)),
            (-67, op0, clienti_db[4], taglio_lungo, time(14, 30)),
            (-63, op0, clienti_db[1], piega, time(16, 0)),
            (-60, op0, clienti_db[5], colore, time(9, 0)),
            (-56, op0, clienti_db[2], cheratina, time(10, 0)),
            (-52, op0, clienti_db[6], taglio_d, time(14, 0)),
            (-49, op0, clienti_db[0], colore_taglio, time(9, 0)),
            (-45, op0, clienti_db[3], balayage, time(10, 30)),
            (-42, op0, clienti_db[7], taglio_d, time(14, 0)),
            (-38, op0, clienti_db[1], piega, time(16, 30)),
            (-35, op0, clienti_db[4], colore, time(9, 0)),
            (-30, op0, clienti_db[5], taglio_lungo, time(10, 0)),
            (-27, op0, clienti_db[0], rigenerante, time(14, 0)),
            (-22, op0, clienti_db[2], colore_taglio, time(9, 30)),
            (-18, op0, clienti_db[6], taglio_d, time(14, 0)),
            (-14, op0, clienti_db[1], balayage, time(9, 0)),
            (-10, op0, clienti_db[3], piega, time(16, 0)),
            (-7, op0, clienti_db[7], colore, time(10, 0)),
            (-4, op0, clienti_db[4], taglio_lungo, time(9, 0)),
            (-2, op0, clienti_db[0], rigenerante, time(14, 0)),
            # Sara (op1) — taglio uomo e barba
            (-83, op1, clienti_db[0], taglio_u, time(9, 0)),
            (-79, op1, clienti_db[3], barba, time(10, 0)),
            (-75, op1, clienti_db[5], taglio_u, time(14, 0)),
            (-71, op1, clienti_db[7], barba, time(9, 30)),
            (-68, op1, clienti_db[0], taglio_u, time(14, 0)),
            (-64, op1, clienti_db[3], barba, time(9, 0)),
            (-61, op1, clienti_db[5], taglio_u, time(10, 0)),
            (-57, op1, clienti_db[7], barba, time(14, 30)),
            (-54, op1, clienti_db[0], taglio_u, time(9, 0)),
            (-50, op1, clienti_db[3], barba, time(10, 30)),
            (-46, op1, clienti_db[5], taglio_u, time(14, 0)),
            (-43, op1, clienti_db[7], barba, time(9, 30)),
            (-40, op1, clienti_db[0], taglio_u, time(14, 0)),
            (-36, op1, clienti_db[3], barba, time(9, 0)),
            (-33, op1, clienti_db[5], taglio_u, time(10, 0)),
            (-29, op1, clienti_db[7], barba, time(14, 0)),
            (-26, op1, clienti_db[0], taglio_u, time(9, 0)),
            (-23, op1, clienti_db[3], barba, time(10, 0)),
            (-19, op1, clienti_db[5], taglio_u, time(14, 30)),
            (-16, op1, clienti_db[7], barba, time(9, 0)),
            (-12, op1, clienti_db[0], taglio_u, time(10, 0)),
            (-9, op1, clienti_db[3], barba, time(14, 0)),
            (-6, op1, clienti_db[5], taglio_u, time(9, 0)),
            (-3, op1, clienti_db[7], barba, time(10, 0)),
            # Marta (op2) — trattamenti e colori speciali
            (-82, op2, clienti_db[1], cheratina, time(9, 0)),
            (-76, op2, clienti_db[2], balayage, time(10, 0)),
            (-72, op2, clienti_db[4], rigenerante, time(14, 0)),
            (-69, op2, clienti_db[6], colore, time(9, 0)),
            (-65, op2, clienti_db[1], cheratina, time(10, 0)),
            (-62, op2, clienti_db[2], balayage, time(14, 0)),
            (-58, op2, clienti_db[4], rigenerante, time(9, 30)),
            (-55, op2, clienti_db[6], colore, time(14, 0)),
            (-51, op2, clienti_db[1], cheratina, time(9, 0)),
            (-48, op2, clienti_db[2], balayage, time(10, 0)),
            (-44, op2, clienti_db[4], rigenerante, time(14, 30)),
            (-41, op2, clienti_db[6], colore, time(9, 0)),
            (-37, op2, clienti_db[1], cheratina, time(10, 0)),
            (-34, op2, clienti_db[2], balayage, time(14, 0)),
            (-31, op2, clienti_db[4], rigenerante, time(9, 0)),
            (-28, op2, clienti_db[6], colore, time(10, 0)),
            (-25, op2, clienti_db[1], cheratina, time(14, 0)),
            (-21, op2, clienti_db[2], balayage, time(9, 30)),
            (-17, op2, clienti_db[4], rigenerante, time(14, 0)),
            (-13, op2, clienti_db[6], colore, time(9, 0)),
            (-8, op2, clienti_db[1], cheratina, time(10, 0)),
            (-5, op2, clienti_db[2], balayage, time(14, 0)),
            (-1, op2, clienti_db[4], rigenerante, time(9, 0)),
            # Clienti ospiti — vari
            (-77, op0, clienti_db[8], taglio_d, time(14, 0)),
            (-73, op1, clienti_db[9], taglio_u, time(9, 0)),
            (-66, op0, clienti_db[10], colore, time(14, 30)),
            (-59, op1, clienti_db[11], barba, time(9, 0)),
            (-53, op2, clienti_db[12], rigenerante, time(14, 0)),
            (-47, op0, clienti_db[13], taglio_d, time(9, 30)),
            (-39, op1, clienti_db[14], taglio_u, time(14, 0)),
            (-32, op0, clienti_db[8], piega, time(9, 0)),
            (-24, op2, clienti_db[9], colore, time(14, 0)),
            (-15, op1, clienti_db[10], barba, time(9, 0)),
            (-11, op0, clienti_db[11], taglio_lungo, time(14, 0)),
        ]

        # Crea prenotazioni passate (pagate, presenti) con alcune eccezioni
        no_show_indici = {5, 18, 33, 48}  # alcune no-show distribuite
        cancellate_indici = {9, 25, 40, 55}  # alcune cancellate

        for i, (offset, operatore, cliente, servizio, ora) in enumerate(storia_passata):
            if i in cancellate_indici:
                crea_prenotazione(
                    cliente,
                    operatore,
                    servizio,
                    offset,
                    ora,
                    stato=StatoPrenotazione.CANCELLATA,
                    stato_pagamento=StatoPagamento.NON_PAGATO,
                    stato_presenza=StatoPresenza.DA_VERIFICARE,
                )
            elif i in no_show_indici:
                p = crea_prenotazione(
                    cliente,
                    operatore,
                    servizio,
                    offset,
                    ora,
                    stato=StatoPrenotazione.COMPLETATA,
                    stato_pagamento=StatoPagamento.NON_PAGATO,
                    stato_presenza=StatoPresenza.NON_PRESENTE,
                )
                if p:
                    p.cliente.contatore_no_show = (p.cliente.contatore_no_show or 0) + 1
                    p.cliente.save(update_fields=['contatore_no_show'])
            else:
                crea_prenotazione(
                    cliente,
                    operatore,
                    servizio,
                    offset,
                    ora,
                    sconto=0.10 if i % 11 == 0 else None,  # sconto occasionale del 10%
                )
            prenotazioni_create += 1

        # --- Futuro: 3 settimane di prenotazioni in arrivo ---
        future = [
            (2, op0, clienti_db[0], taglio_d, time(9, 0)),
            (2, op1, clienti_db[3], barba, time(10, 0)),
            (2, op2, clienti_db[1], cheratina, time(9, 0)),
            (3, op0, clienti_db[2], colore_taglio, time(14, 0)),
            (3, op1, clienti_db[5], taglio_u, time(9, 30)),
            (4, op2, clienti_db[4], balayage, time(10, 0)),
            (5, op0, clienti_db[6], piega, time(16, 0)),
            (5, op1, clienti_db[7], barba, time(9, 0)),
            (6, op2, clienti_db[2], rigenerante, time(14, 30)),
            (7, op0, clienti_db[1], taglio_lungo, time(9, 0)),
            (7, op1, clienti_db[0], taglio_u, time(10, 0)),
            (8, op2, clienti_db[3], colore, time(14, 0)),
            (9, op0, clienti_db[4], colore_taglio, time(9, 30)),
            (10, op1, clienti_db[5], barba, time(9, 0)),
            (10, op2, clienti_db[6], cheratina, time(10, 0)),
            (12, op0, clienti_db[7], taglio_d, time(14, 0)),
            (12, op1, clienti_db[0], taglio_u, time(9, 0)),
            (13, op2, clienti_db[1], balayage, time(9, 0)),
            (14, op0, clienti_db[2], piega, time(16, 0)),
            (15, op1, clienti_db[3], barba, time(10, 0)),
        ]

        for offset, operatore, cliente, servizio, ora in future:
            p = crea_prenotazione(
                cliente,
                operatore,
                servizio,
                offset,
                ora,
                stato=StatoPrenotazione.CONFERMATA,
                stato_pagamento=StatoPagamento.NON_PAGATO,
                stato_presenza=StatoPresenza.DA_VERIFICARE,
            )
            if p:
                prenotazioni_create += 1

        self.stdout.write(f'  ✓ {prenotazioni_create} prenotazioni create')

        # ------------------------------------------------------------------
        # Aggiorna cliente con 3 no-show per vederlo "bloccato"
        # ------------------------------------------------------------------
        self.stdout.write('Cliente bloccato (3 no-show)...')
        if len(clienti_db) > 14:
            bloccato = clienti_db[14]  # Teresa Martinelli
            bloccato.contatore_no_show = 3
            bloccato.bloccato = True
            bloccato.save(update_fields=['contatore_no_show', 'bloccato'])
            self.stdout.write(f'  ✓ {bloccato.nome} bloccata (contatore_no_show=3)')

        # ------------------------------------------------------------------
        # Notifiche di esempio
        # ------------------------------------------------------------------
        self.stdout.write('Notifiche...')
        notifiche_create = 0
        utenti_con_notifiche = [
            u
            for u, _ in [
                User.objects.get_or_create(email=d['email']) for d in CLIENTI_REGISTRATI[:5]
            ]
        ]
        for utente in utenti_con_notifiche:
            Notifica.objects.get_or_create(
                destinatario=utente,
                tipo=TipoNotifica.CONFERMA_PRENOTAZIONE,
                defaults={
                    'titolo': 'Prenotazione confermata',
                    'messaggio': 'Il tuo appuntamento è confermato. Ti aspettiamo!',
                    'link': '/le-mie-prenotazioni',
                    'letta': random.choice([True, False]),
                },
            )
            notifiche_create += 1
        # Notifica non letta per l'admin
        Notifica.objects.get_or_create(
            destinatario=admin,
            tipo=TipoNotifica.CLIENTE_BLOCCATO,
            defaults={
                'titolo': 'Cliente bloccata per no-show',
                'messaggio': (
                    'Teresa Martinelli è stata bloccata automaticamente '
                    '(3 mancate presentazioni, soglia 3).'
                ),
                'link': '/clienti',
                'letta': False,
            },
        )
        notifiche_create += 1
        self.stdout.write(f'  ✓ {notifiche_create} notifiche')

        # ------------------------------------------------------------------
        # Riepilogo finale
        # ------------------------------------------------------------------
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('DATABASE POPOLATO CON SUCCESSO'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write('Accessi (tutti con password: ' + PASSWORD_DEMO + ')')
        self.stdout.write('')
        self.stdout.write('  AMMINISTRATORE:')
        self.stdout.write('    admin@salone.demo')
        self.stdout.write('')
        self.stdout.write('  OPERATRICI:')
        for d in OPERATRICI:
            self.stdout.write(f'    {d["email"]}  ({d["operatore_nome"]})')
        self.stdout.write('')
        self.stdout.write('  CLIENTI REGISTRATI:')
        for d in CLIENTI_REGISTRATI:
            self.stdout.write(f'    {d["email"]}')
        self.stdout.write('')
        self.stdout.write('  Note:')
        self.stdout.write('  - Cliente bloccata: Teresa Martinelli (3 no-show)')
        self.stdout.write(
            '  - Prenotazioni passate: pagate e presenti, alcune no-show e cancellate'
        )
        self.stdout.write('  - Prenotazioni future: confermate per le prossime 2 settimane')
        self.stdout.write("  - Notifica non letta nell'admin: cliente bloccata")
