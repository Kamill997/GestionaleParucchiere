"""Logica di business delle prenotazioni (docs/esempio-settore-parrucchiere.md,
"Logica di business specifica delle prenotazioni"). Tenuta separata da
serializer/viewset per restare facilmente testabile in isolamento.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Case, Count, Q, Sum, When
from django.utils import timezone

from apps.clienti.models import Cliente
from apps.operatori.models import Disponibilita, EccezioneDisponibilita, Operatore
from apps.servizi.models import Servizio
from apps.settings_app.models import get_int

from .models import Prenotazione, StatoPagamento, StatoPrenotazione, StatoPresenza


def calcola_slot(
    operatore: Operatore,
    servizio: Servizio,
    giorno: date,
    escludi_prenotazione_id=None,
    escludi_passati: bool = False,
    durata_totale_minuti: int | None = None,
) -> list[dict]:
    """Tutti gli slot per operatore+servizio in un giorno dato.
    Ogni elemento è un dizionario:
      {'inizio': datetime, 'fine': datetime, 'disponibile': bool}

    Uno slot ha disponibile=True se non confligge con nessuna Prenotazione
    attiva dell'operatore (incluso il buffer prima e dopo ciascuna prenotazione).
    Se confligge con una prenotazione attiva, disponibile=False.

    Se `escludi_passati` è True e `giorno == timezone.localdate()`:
    gli orari d'inizio già trascorsi (inizio <= timezone.now()) vengono omessi
    completamente, in modo che i clienti non vedano orari passati nella giornata odierna.
    """
    buffer = timedelta(minutes=get_int('buffer_minuti_prenotazioni'))
    passo = timedelta(minutes=get_int('intervallo_slot_minuti'))
    durata = timedelta(minutes=durata_totale_minuti or servizio.durata_minuti)
    tz = timezone.get_current_timezone()
    ora_corrente = timezone.now()
    oggi = timezone.localdate()

    turni = operatore.disponibilita.filter(giorno_settimana=giorno.weekday())
    prenotazioni_del_giorno = list(
        operatore.prenotazioni.exclude(stato=StatoPrenotazione.CANCELLATA)
        .exclude(pk=escludi_prenotazione_id)
        .filter(inizio__date=giorno)
    )

    eccezioni = list(
        EccezioneDisponibilita.objects.filter(
            Q(operatore=operatore) | Q(operatore__isnull=True),
            data_inizio__lte=giorno,
            data_fine__gte=giorno,
        )
    )

    # Se c'è una chiusura o ferie per l'intera giornata (senza orari specificati), nessun slot è generabile
    chiusura_giornaliera = any(e.ora_inizio is None and e.ora_fine is None for e in eccezioni)
    if chiusura_giornaliera:
        return []

    # Fasce orarie coperte da eccezioni parziali (permessi, assenze orarie)
    fasce_eccezioni = []
    for e in eccezioni:
        if e.ora_inizio and e.ora_fine:
            dt_inizio_ecc = timezone.make_aware(datetime.combine(giorno, e.ora_inizio), tz)
            dt_fine_ecc = timezone.make_aware(datetime.combine(giorno, e.ora_fine), tz)
            fasce_eccezioni.append((dt_inizio_ecc, dt_fine_ecc))

    slot_list = []
    for turno in turni:
        inizio_turno = timezone.make_aware(datetime.combine(giorno, turno.ora_inizio), tz)
        fine_turno = timezone.make_aware(datetime.combine(giorno, turno.ora_fine), tz)

        cursore = inizio_turno
        while cursore + durata <= fine_turno:
            fine_slot = cursore + durata

            # Se richiesto ed è la data odierna, salta gli slot già passati rispetto ad adesso
            if escludi_passati and giorno == oggi and cursore <= ora_corrente:
                cursore += passo
                continue

            confligge_prenotazione = any(
                (cursore - buffer) < p.fine and (fine_slot + buffer) > p.inizio
                for p in prenotazioni_del_giorno
            )
            confligge_eccezione = any(
                cursore < dt_fine and fine_slot > dt_inizio
                for dt_inizio, dt_fine in fasce_eccezioni
            )
            confligge = confligge_prenotazione or confligge_eccezione

            slot_list.append({
                'inizio': cursore,
                'fine': fine_slot,
                'disponibile': not confligge,
            })
            cursore += passo

    return slot_list


def calcola_slot_liberi(
    operatore: Operatore,
    servizio: Servizio,
    giorno: date,
    escludi_prenotazione_id=None,
    durata_totale_minuti: int | None = None,
) -> list[tuple[datetime, datetime]]:
    """Slot [inizio, fine) liberi per operatore+servizio in un giorno dato.

    Uno slot e' libero se rientra in un turno di Disponibilita' per quel
    giorno della settimana, e non confligge con nessuna Prenotazione
    attiva (non cancellata) dello stesso operatore una volta applicato il
    buffer configurato prima e dopo ciascuna prenotazione esistente.

    `escludi_prenotazione_id`: da passare quando si ricalcola la
    disponibilita' per un reschedule, altrimenti la prenotazione stessa
    (ancora presente nel DB col vecchio orario finche' non viene salvata)
    risulterebbe in conflitto con se stessa.
    """
    tutti = calcola_slot(
        operatore,
        servizio,
        giorno,
        escludi_prenotazione_id=escludi_prenotazione_id,
        escludi_passati=False,
        durata_totale_minuti=durata_totale_minuti,
    )
    return [(s['inizio'], s['fine']) for s in tutti if s['disponibile']]


def slot_e_disponibile(
    operatore: Operatore,
    servizio: Servizio,
    inizio: datetime,
    escludi_prenotazione_id=None,
    durata_totale_minuti: int | None = None,
) -> bool:
    """Ricontrollo puntuale usato in validazione (oltre al vincolo DB, vedi
    models.Prenotazione.Meta.constraints): copre anche il buffer, che il
    vincolo a livello di database non applica."""
    durata_effettiva = durata_totale_minuti or servizio.durata_minuti
    giorno = timezone.localtime(inizio).date()
    fine = inizio + timedelta(minutes=durata_effettiva)
    return any(
        slot_inizio == inizio and slot_fine == fine
        for slot_inizio, slot_fine in calcola_slot_liberi(
            operatore,
            servizio,
            giorno,
            escludi_prenotazione_id=escludi_prenotazione_id,
            durata_totale_minuti=durata_effettiva,
        )
    )


def puo_cancellare_liberamente(prenotazione: Prenotazione) -> bool:
    """Policy di cancellazione (docs/esempio-settore-parrucchiere.md):
    cancellabile gratuitamente fino a N ore prima (default 24, configurabile
    in Impostazioni). Oltre la soglia, un Cliente non puo' piu' auto-cancellare
    (lo staff puo' comunque farlo, vedi apps/prenotazioni/views.py)."""
    ore_preavviso = get_int('ore_preavviso_cancellazione')
    return timezone.now() <= prenotazione.inizio - timedelta(hours=ore_preavviso)


def segna_presenza(prenotazione: Prenotazione, nuovo_stato: str, *, autore=None) -> Prenotazione:
    """docs/08-pagamenti.md, "Politica no-show". Se la nuova marcatura e'
    'non_presente', incrementa il contatore del cliente e lo blocca se la
    soglia configurabile viene raggiunta/superata.

    Non invia l'email di avviso descritta nei docs (richiede il modulo
    Notifiche, non ancora costruito): registra pero' il blocco in
    AuditLog, cosi' la decisione resta tracciata anche senza email.
    """
    stato_precedente = prenotazione.stato_presenza
    prenotazione.stato_presenza = nuovo_stato

    # Quando un appuntamento confermato viene marcato come presente,
    # lo stato avanza automaticamente a completata: cosi' lo staff ha
    # un riscontro chiaro nella tabella gestione prenotazioni
    # (docs/08-pagamenti.md, tracciamento presenza).
    update_fields = ['stato_presenza']
    if (
        nuovo_stato == StatoPresenza.PRESENTE
        and prenotazione.stato == StatoPrenotazione.CONFERMATA
    ):
        prenotazione.stato = StatoPrenotazione.COMPLETATA
        update_fields.append('stato')

    prenotazione.save(update_fields=update_fields)

    appena_diventata_non_presente = (
        nuovo_stato == StatoPresenza.NON_PRESENTE and stato_precedente != StatoPresenza.NON_PRESENTE
    )
    if appena_diventata_non_presente:
        cliente = prenotazione.cliente
        cliente.contatore_no_show += 1
        soglia = get_int('soglia_no_show')
        appena_bloccato = cliente.contatore_no_show >= soglia and not cliente.bloccato
        if appena_bloccato:
            cliente.bloccato = True
        cliente.save(update_fields=['contatore_no_show', 'bloccato'])

        if appena_bloccato:
            from apps.audit_log.models import AuditLog

            AuditLog.objects.create(
                user=autore,
                azione='cliente_bloccato_no_show',
                entita_coinvolta=f'Cliente:{cliente.id}',
                dettagli={'contatore_no_show': cliente.contatore_no_show, 'soglia': soglia},
            )

            # docs/08-pagamenti.md, "Notifiche collegate": avviso al cliente
            # (completa l'ultimo punto ancora aperto del checklist di questo
            # file) + notifica interna a tutti gli Amministratori.
            from apps.notifiche.models import TipoNotifica
            from apps.notifiche.services import notifica_amministratori, notifica_cliente

            notifica_cliente(
                cliente,
                TipoNotifica.SOGLIA_NO_SHOW_RAGGIUNTA,
                'Prenotazioni bloccate per mancate presentazioni',
                f'Hai raggiunto {cliente.contatore_no_show} mancate presentazioni al salone. '
                'Le tue prenotazioni future sono bloccate: contatta il salone per sbloccarle.',
            )
            notifica_amministratori(
                TipoNotifica.CLIENTE_BLOCCATO,
                'Cliente bloccato per no-show',
                f"{cliente.nome} e' stato bloccato automaticamente "
                f'({cliente.contatore_no_show} mancate presentazioni, soglia {soglia}).',
                link='/clienti',
            )

    return prenotazione


def sblocca_cliente(cliente, *, autore=None) -> None:
    """Sblocco manuale (docs/08-pagamenti.md: "non deve essere permanente
    per definizione"). Il contatore no-show resta come storico: si azzera
    solo il blocco, non le mancate presentazioni passate."""
    if not cliente.bloccato:
        return
    cliente.bloccato = False
    cliente.save(update_fields=['bloccato'])

    from apps.audit_log.models import AuditLog

    AuditLog.objects.create(
        user=autore,
        azione='cliente_sbloccato',
        entita_coinvolta=f'Cliente:{cliente.id}',
        dettagli={},
    )

    from apps.notifiche.models import TipoNotifica
    from apps.notifiche.services import notifica_amministratori

    notifica_amministratori(
        TipoNotifica.CLIENTE_SBLOCCATO,
        'Cliente sbloccato',
        f"{cliente.nome} e' stato sbloccato manualmente.",
        link='/clienti',
    )


def calcola_kpi_dashboard(
    oggi: date | None = None,
    operatore: Operatore | None = None,
    e_amministratore: bool = True,
) -> dict:
    """KPI di sintesi per la dashboard.
    Se operatore è specificato (o e_amministratore=False), le metriche di appuntamenti
    e occupazione sono filtrate per il singolo operatore e il fatturato viene omesso.
    """
    oggi = oggi or timezone.localdate()
    fine_settimana = oggi + timedelta(days=7)

    prenotazioni_attive = Prenotazione.objects.exclude(stato=StatoPrenotazione.CANCELLATA)
    if operatore:
        prenotazioni_attive = prenotazioni_attive.filter(operatore=operatore)

    prenotazioni_oggi = prenotazioni_attive.filter(inizio__date=oggi).count()
    prenotazioni_settimana = prenotazioni_attive.filter(
        inizio__date__gte=oggi, inizio__date__lt=fine_settimana
    ).count()

    servizio_top = (
        prenotazioni_attive.values('servizio__nome')
        .annotate(conteggio=Count('id'))
        .order_by('-conteggio')
        .first()
    )

    minuti_disponibili = 0
    disp_qs = Disponibilita.objects.filter(giorno_settimana=oggi.weekday())
    if operatore:
        disp_qs = disp_qs.filter(operatore=operatore)
    for disp in disp_qs.select_related('operatore'):
        inizio_dt = datetime.combine(date.min, disp.ora_inizio)
        fine_dt = datetime.combine(date.min, disp.ora_fine)
        minuti_disponibili += (fine_dt - inizio_dt).total_seconds() / 60

    minuti_prenotati = sum(
        p.servizio.durata_minuti
        for p in prenotazioni_attive.filter(inizio__date=oggi).select_related('servizio')
    )

    tasso_occupazione_oggi = (
        round(100 * minuti_prenotati / minuti_disponibili, 1) if minuti_disponibili > 0 else 0.0
    )

    if e_amministratore:
        fatturato_settimana = (
            prenotazioni_attive.filter(
                inizio__date__gte=oggi,
                inizio__date__lt=fine_settimana,
                stato_pagamento=StatoPagamento.PAGATO,
            ).aggregate(totale=Sum('importo'))['totale']
            or 0
        )
        fatturato_str = str(fatturato_settimana)
    else:
        fatturato_str = None

    presenze_valutate = prenotazioni_attive.filter(
        inizio__date__lt=oggi,
        stato_presenza__in=[StatoPresenza.PRESENTE, StatoPresenza.NON_PRESENTE],
    )
    totale_valutate = presenze_valutate.count()
    non_presentati = presenze_valutate.filter(stato_presenza=StatoPresenza.NON_PRESENTE).count()
    tasso_no_show = round(100 * non_presentati / totale_valutate, 1) if totale_valutate > 0 else 0.0

    return {
        'prenotazioni_oggi': prenotazioni_oggi,
        'prenotazioni_settimana': prenotazioni_settimana,
        'servizio_piu_richiesto': (
            {'nome': servizio_top['servizio__nome'], 'conteggio': servizio_top['conteggio']}
            if servizio_top
            else None
        ),
        'tasso_occupazione_oggi': tasso_occupazione_oggi,
        'fatturato_settimana': fatturato_str,
        'tasso_no_show': tasso_no_show,
    }


def calcola_report_guadagni(oggi: date | None = None) -> dict:
    """docs/08-pagamenti.md, "Dashboard guadagni (lato Amministratore)":
    ultimo pezzo del checklist del modulo pagamenti rimasto scoperto finora
    (calcola_kpi_dashboard sopra copre solo il totale aggregato). Qui si
    aggiungono le tre viste ancora mancanti:
    - "Guadagni per servizio/categoria e per operatore" (ultimi 7 giorni,
      stessa finestra di fatturato_settimana, solo prenotazioni pagate)
    - "Guadagni per cliente" (storico completo, non solo la settimana:
      il testo dei docs dice esplicitamente "somma storica per cliente,
      utile anche per individuare i clienti di maggior valore")
    - "elenco dei clienti vicini alla soglia di blocco" (resa possibile
      dal tracciamento presenze di segna_presenza sopra)

    Non sostituisce calcola_kpi_dashboard (restato invariato, usato dalla
    Dashboard generale Amministratore+Operatore): questa e' una vista piu'
    di dettaglio, riservata al solo Amministratore a livello di view
    (vedi views.ReportGuadagniView), coerente col titolo della sezione nei
    docs ("lato Amministratore").
    """
    oggi = oggi or timezone.localdate()
    fine_settimana = oggi + timedelta(days=7)

    prenotazioni_attive = Prenotazione.objects.exclude(stato=StatoPrenotazione.CANCELLATA)
    pagate_settimana = prenotazioni_attive.filter(
        inizio__date__gte=oggi,
        inizio__date__lt=fine_settimana,
        stato_pagamento=StatoPagamento.PAGATO,
    )

    per_servizio = (
        pagate_settimana.values('servizio__nome')
        .annotate(totale=Sum('importo'))
        .order_by('-totale')
    )
    per_operatore = (
        pagate_settimana.values('operatore__nome')
        .annotate(totale=Sum('importo'))
        .order_by('-totale')
    )
    # Storico completo (non solo la settimana), coerente con "somma storica
    # per cliente" nei docs; limitato ai primi 10 - e' pensato per
    # individuare i clienti di maggior valore, non come esportazione dati.
    top_clienti = (
        prenotazioni_attive.filter(stato_pagamento=StatoPagamento.PAGATO)
        .values('cliente__nome')
        .annotate(totale=Sum('importo'))
        .order_by('-totale')[:10]
    )

    soglia = get_int('soglia_no_show')
    # "Vicini alla soglia": a un solo no-show di distanza dal blocco
    # automatico, ma non ancora bloccati (un cliente gia' bloccato non e'
    # "vicino", ci e' gia' arrivato - vedi segna_presenza sopra).
    clienti_vicini_al_blocco = Cliente.objects.filter(
        bloccato=False, contatore_no_show__gte=max(soglia - 1, 1)
    ).values('nome', 'contatore_no_show')

    return {
        'per_servizio': [
            {'nome': riga['servizio__nome'], 'totale': str(riga['totale'])} for riga in per_servizio
        ],
        'per_operatore': [
            {'nome': riga['operatore__nome'], 'totale': str(riga['totale'])}
            for riga in per_operatore
        ],
        'top_clienti': [
            {'nome': riga['cliente__nome'], 'totale': str(riga['totale'])} for riga in top_clienti
        ],
        'clienti_vicini_al_blocco': [
            {'nome': riga['nome'], 'contatore_no_show': riga['contatore_no_show'], 'soglia': soglia}
            for riga in clienti_vicini_al_blocco
        ],
    }


def processa_lista_attesa_per_cancellazione(prenotazione):
    """Quando una prenotazione viene cancellata, cerca la prima richiesta
    compatibile in lista d'attesa (stessa data, stesso servizio, operatore
    uguale o non specificato) e la notifica via in-app ed email.
    """
    from apps.notifiche.models import TipoNotifica
    from apps.notifiche.services import notifica_cliente

    from .models import RichiestaListaAttesa, StatoListaAttesa

    inizio_locale = timezone.localtime(prenotazione.inizio)
    giorno = inizio_locale.date()
    ora_inizio = inizio_locale.time()

    # Query di base: richieste in attesa per la stessa data e servizio
    candidati = RichiestaListaAttesa.objects.filter(
        data=giorno,
        servizio=prenotazione.servizio,
        stato=StatoListaAttesa.IN_ATTESA,
    ).filter(
        Q(operatore=prenotazione.operatore) | Q(operatore__isnull=True)
    )

    # Escludi il cliente che ha appena cancellato (se presente in lista)
    candidati = candidati.exclude(cliente=prenotazione.cliente)

    # Ordina: dai priorità a chi ha indicato esattamente questo orario preferito,
    # poi ordina cronologicamente FIFO (creato_il)
    candidato = candidati.order_by(
        Case(
            When(ora_preferita=ora_inizio, then=0),
            When(ora_preferita__isnull=True, then=1),
            default=2,
        ),
        'creato_il',
    ).first()

    if not candidato:
        return None

    # Aggiorna lo stato della richiesta
    candidato.stato = StatoListaAttesa.NOTIFICATO
    candidato.notificato_il = timezone.now()
    candidato.save(update_fields=['stato', 'notificato_il'])

    # Invia notifica automatica in-app + email
    data_str = giorno.strftime('%d/%m/%Y')
    ora_str = inizio_locale.strftime('%H:%M')
    op_str = prenotazione.operatore.nome
    serv_str = prenotazione.servizio.nome

    notifica_cliente(
        candidato.cliente,
        TipoNotifica.DISPONIBILITA_LISTA_ATTESA,
        "Posto disponibile dalla lista d'attesa!",
        f"Si è liberato un appuntamento per {serv_str} con {op_str} "
        f"il {data_str} alle ore {ora_str}. "
        "Prenota subito prima che lo slot venga occupato!",
        link=f"/prenota?servizio={prenotazione.servizio.id}&operatore={prenotazione.operatore.id}&data={giorno.isoformat()}",
    )

    return candidato


def calcola_andamento_profitti(giorni: int = 30, fine_giorno: date | None = None) -> dict:
    """Calcola l'andamento del fatturato giornaliero degli ultimi N giorni
    e la ripartizione per categoria di servizio e per operatore.
    Riservato alla dashboard amministratore per grafici lineari e a torta.
    """
    fine_giorno = fine_giorno or timezone.localdate()
    inizio_periodo = fine_giorno - timedelta(days=giorni - 1)

    prenotazioni_periodo = (
        Prenotazione.objects.filter(
            stato_pagamento=StatoPagamento.PAGATO,
            inizio__date__gte=inizio_periodo,
            inizio__date__lte=fine_giorno,
        )
        .exclude(stato=StatoPrenotazione.CANCELLATA)
        .select_related('servizio', 'operatore')
    )

    # Inizializza tutti i giorni dell'intervallo con totale 0
    per_giorno_dict = {}
    giorno_corrente = inizio_periodo
    while giorno_corrente <= fine_giorno:
        per_giorno_dict[giorno_corrente] = {'totale': Decimal('0.00'), 'appuntamenti': 0}
        giorno_corrente += timedelta(days=1)

    categorie_dict = {}
    operatori_dict = {}
    totale_complessivo = Decimal('0.00')

    for p in prenotazioni_periodo:
        d = p.inizio.date()
        if d in per_giorno_dict:
            per_giorno_dict[d]['totale'] += p.importo
            per_giorno_dict[d]['appuntamenti'] += 1

        cat = p.servizio.categoria if (p.servizio and p.servizio.categoria) else 'Altro'
        if cat not in categorie_dict:
            categorie_dict[cat] = {'totale': Decimal('0.00'), 'appuntamenti': 0}
        categorie_dict[cat]['totale'] += p.importo
        categorie_dict[cat]['appuntamenti'] += 1

        op_nome = p.operatore.nome if p.operatore else 'Non assegnato'
        if op_nome not in operatori_dict:
            operatori_dict[op_nome] = {'totale': Decimal('0.00'), 'appuntamenti': 0}
        operatori_dict[op_nome]['totale'] += p.importo
        operatori_dict[op_nome]['appuntamenti'] += 1

        totale_complessivo += p.importo

    andamento_giornaliero = [
        {
            'data': d.isoformat(),
            'etichetta': d.strftime('%d/%m'),
            'totale': float(dati['totale']),
            'appuntamenti': dati['appuntamenti'],
        }
        for d, dati in sorted(per_giorno_dict.items())
    ]

    categorie_list = [
        {
            'categoria': cat,
            'totale': float(dati['totale']),
            'appuntamenti': dati['appuntamenti'],
            'percentuale': round(float(dati['totale'] / totale_complessivo * 100), 1)
            if totale_complessivo > 0
            else 0.0,
        }
        for cat, dati in sorted(categorie_dict.items(), key=lambda x: x[1]['totale'], reverse=True)
    ]

    operatori_list = [
        {
            'operatore': op,
            'totale': float(dati['totale']),
            'appuntamenti': dati['appuntamenti'],
        }
        for op, dati in sorted(operatori_dict.items(), key=lambda x: x[1]['totale'], reverse=True)
    ]

    return {
        'totale_periodo': float(totale_complessivo),
        'media_giornaliera': round(float(totale_complessivo / giorni), 2),
        'giorni': andamento_giornaliero,
        'categorie': categorie_list,
        'operatori': operatori_list,
    }

