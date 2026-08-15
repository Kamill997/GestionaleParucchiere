# Caso Studio: Gestionale per Salone di Parrucchiere

## Premessa

Questo documento applica lo scheletro generico al caso concreto di un salone di parrucchiere/centro estetico, con prenotazioni online, catalogo servizi, notifiche e gestione completa sia lato cliente sia lato amministratore.

## Ruoli utente

| Ruolo | Chi è | Cosa può fare |
|---|---|---|
| **Cliente** | Chi prenota un servizio | Sfoglia il catalogo, prenota/modifica/cancella i propri appuntamenti, riceve notifiche, vede lo storico |
| **Operatore** | Il professionista che eroga il servizio | Vede il proprio calendario, gestisce la propria disponibilità, segna gli appuntamenti come completati/no-show |
| **Amministratore** | Chi gestisce il salone | Tutto quello che fa l'operatore, più: gestione catalogo, staff, tutte le prenotazioni, reportistica, impostazioni |

## Entità di dominio

| Entità generica | Diventa | Campi principali |
|---|---|---|
| Anagrafiche | **Servizi** | nome, descrizione, categoria, durata in minuti, prezzo, foto |
| Anagrafiche | **Operatori** | nome, foto, specializzazioni, collegamento a un account utente |
| Anagrafiche | **Clienti** | nome, contatti, preferenze/note, storico servizi |
| (nuova) | **Prenotazioni** | cliente, operatore, servizio, data/ora inizio/fine, stato, note |
| (nuova) | **Disponibilità operatore** | turni settimanali standard + eccezioni |

## Funzionalità lato Cliente

1. Catalogo servizi
2. Prenotazione (servizio, operatore, slot liberi, conferma)
3. Gestione delle proprie prenotazioni (modifica/cancella nel rispetto della policy)
4. Notifiche
5. Storico

## Funzionalità lato Amministratore/Staff

1. Gestione catalogo servizi
2. Gestione staff
3. Calendario prenotazioni
4. Gestione prenotazioni (conferma, modifica, cancellazione, marcatura presenza)
5. Gestione clienti (note interne non visibili al cliente)
6. Notifiche e promozioni
7. Reportistica (fatturato, servizi più richiesti, tasso no-show, occupazione)
8. Impostazioni

## Logica di business specifica delle prenotazioni

- **Calcolo della disponibilità**: turno operatore + non sovrapposizione + buffer
- **Prevenzione doppia prenotazione**: applicativa + vincolo a livello di database (indice di esclusione PostgreSQL)
- **Policy di cancellazione**: da definire esplicitamente (es. gratuita fino a 24h prima)
- **No-show**: tracciamento per statistiche e limitazione clienti recidivi (vedi `08-pagamenti.md`)

## Cosa resta invariato rispetto allo scheletro generico

- Autenticazione, RBAC, sicurezza
- PWA
- Docker/CI-CD
- Import/Export (utile in fase di avvio per l'anagrafica clienti esistente)

## Cosa si aggiunge rispetto allo scheletro generico

- Modulo Calendario/Disponibilità
- Dashboard con KPI specifici del settore
- Reportistica con metriche specifiche (occupazione per operatore, tasso di no-show)

## Nota

Se tra le note cliente si raccolgono informazioni assimilabili a dati sulla salute, va trattata con l'attenzione aggiuntiva che il GDPR riserva alle categorie particolari di dati.

## Checklist riassuntiva

- [x] Ruoli Cliente / Operatore / Amministratore configurati con permessi corretti
- [x] Catalogo servizi con categorie, prezzi, durate
- [x] Calcolo disponibilità funzionante (turni + prenotazioni esistenti + buffer)
- [x] Prevenzione doppia prenotazione verificata anche in caso di richieste simultanee
- [x] Policy di cancellazione definita e mostrata chiaramente al cliente
- [ ] Notifiche di conferma, promemoria e cancellazione funzionanti (modulo Notifiche non ancora costruito)
- [x] Calendario amministrativo per operatore/salone
- [x] Reportistica di base (fatturato, occupazione, no-show)
- [x] Import dell'anagrafica clienti esistente
