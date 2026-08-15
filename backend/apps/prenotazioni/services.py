"""Logica di business delle prenotazioni (docs/esempio-settore-parrucchiere.md,
"Logica di business specifica delle prenotazioni"). Tenuta separata da
serializer/viewset per restare facilmente testabile in isolamento.
"""

from datetime import date, datetime, timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from apps.clienti.models import Cliente
from apps.operatori.models import Disponibilita, Operatore
from apps.servizi.models import Servizio
from apps.settings_app.models import get_int

from .models import Prenotazione, StatoPagamento, StatoPrenotazione, StatoPresenza


def calcola_slot_liberi(
    operatore: Operatore,
    servizio: Servizio,
    giorno: date,
    escludi_prenotazione_id=None,
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
    buffer = timedelta(minutes=get_int('buffer_minuti_prenotazioni'))
    passo = timedelta(minutes=get_int('intervallo_slot_minuti'))
    durata = timedelta(minutes=servizio.durata_minuti)
    tz = timezone.get_current_timezone()

    turni = operatore.disponibilita.filter(giorno_settimana=giorno.weekday())
    prenotazioni_del_giorno = list(
        operatore.prenotazioni.exclude(stato=StatoPrenotazione.CANCELLATA)
        .exclude(pk=escludi_prenotazione_id)
        .filter(inizio__date=giorno)
    )

    slot_liberi = []
    for turno in turni:
        inizio_turno = timezone.make_aware(datetime.combine(giorno, turno.ora_inizio), tz)
        fine_turno = timezone.make_aware(datetime.combine(giorno, turno.ora_fine), tz)

        cursore = inizio_turno
        while cursore + durata <= fine_turno:
            fine_slot = cursore + durata
            confligge = any(
                (cursore - buffer) < p.fine and (fine_slot + buffer) > p.inizio
                for p in prenotazioni_del_giorno
            )
            if not confligge:
                slot_liberi.append((cursore, fine_slot))
            cursore += passo

    return slot_liberi


def slot_e_disponibile(
    operatore: Operatore, servizio: Servizio, inizio: datetime, escludi_prenotazione_id=None
) -> bool:
    """Ricontrollo puntuale usato in validazione (oltre al vincolo DB, vedi
    models.Prenotazione.Meta.constraints): copre anche il buffer, che il
    vincolo a livello di database non applica."""
    giorno = timezone.localtime(inizio).date()
    fine = inizio + timedelta(minutes=servizio.durata_minuti)
    return any(
        slot_inizio == inizio and slot_fine == fine
        for slot_inizio, slot_fine in calcola_slot_liberi(
            operatore, servizio, giorno, escludi_prenotazione_id=escludi_prenotazione_id
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
    prenotazione.save(update_fields=['stato_presenza'])

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


def calcola_kpi_dashboard(oggi: date | None = None) -> dict:
    """KPI di sintesi per la dashboard amministrativa
    (docs/esempio-settore-parrucchiere.md: "prenotazioni di oggi, tasso di
    occupazione della giornata, fatturato del periodo, servizi piu' richiesti").
    """
    oggi = oggi or timezone.localdate()
    fine_settimana = oggi + timedelta(days=7)

    prenotazioni_attive = Prenotazione.objects.exclude(stato=StatoPrenotazione.CANCELLATA)

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
    for disp in Disponibilita.objects.filter(giorno_settimana=oggi.weekday()).select_related(
        'operatore'
    ):
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

    # docs/08-pagamenti.md: "Guadagni totali per periodo, sommando il
    # prezzo delle prenotazioni con stato_pagamento = pagato" - solo ora
    # possibile, il tracciamento pagamenti non esisteva prima di questa fase.
    fatturato_settimana = (
        prenotazioni_attive.filter(
            inizio__date__gte=oggi,
            inizio__date__lt=fine_settimana,
            stato_pagamento=StatoPagamento.PAGATO,
        ).aggregate(totale=Sum('importo'))['totale']
        or 0
    )

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
        'fatturato_settimana': str(fatturato_settimana),
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
