# Importazione ed Esportazione Dati in Blocco

## Perché serve

Quasi ogni gestionale reale, al momento dell'onboarding di un nuovo cliente, deve poter importare dati già esistenti. Allo stesso modo, prima o poi viene quasi sempre richiesta anche l'esportazione.

## Formati supportati

| Formato | Uso tipico |
|---|---|
| CSV | Il più universale |
| Excel (.xlsx) | Preferito dagli utenti non tecnici |
| JSON | Utile per integrazioni API-to-API |

## Flusso di importazione

1. Upload del file
2. Parsing e anteprima
3. Mappatura colonne (o colonne fisse da template, per implementazioni ridotte — vedi nota sotto)
4. Validazione riga per riga, riusando lo stesso serializer DRF della creazione manuale
5. Conferma ed elaborazione
6. Report finale (righe importate, fallite e perché)

## Gestione file grandi: elaborazione asincrona

Per file oltre poche centinaia di righe, elaborazione in coda (Celery) invece che sincrona.

> **Nota di implementazione (questo progetto):** per i volumi realistici di un singolo salone, l'implementazione di riferimento usa elaborazione **sincrona** e **colonne fisse da template** invece del mappatore interattivo, come semplificazione deliberata — vedi README del progetto.

## Deduplica

Chiave di match (es. email per i clienti): se il record esiste già, aggiornare, mai sovrascrivere silenziosamente. Duplicati interni al file segnalati esplicitamente nel report.

## Template di importazione

Fornire un file CSV/Excel di esempio scaricabile con le intestazioni corrette e una riga di esempio.

## Flusso di esportazione

- **Esportazione filtrata**: rispettare i filtri/ricerca attivi
- **Esportazione completa**: sincrona per dataset piccoli, asincrona (coda + notifica) per dataset grandi
- Link di download con scadenza se il file resta su storage pubblico

## Sicurezza

- Validare tipo e dimensione del file in upload
- RBAC: import/export riservati a ruoli specifici (spesso solo admin/manager)
- Registrare ogni importazione/esportazione nell'audit log

## Librerie consigliate

| Livello | Libreria | Uso |
|---|---|---|
| Frontend | **papaparse** | Parsing CSV lato client |
| Frontend | **SheetJS (xlsx)** | Lettura/scrittura Excel lato client |
| Backend | **pandas** | Parsing/validazione CSV ed Excel lato server |
| Backend | **openpyxl** | Lettura/scrittura Excel con controllo fine |
| Backend | **Celery** | Elaborazione asincrona a lotti (per implementazioni non ridotte) |

## Checklist

- [x] Componente di upload (implementazione ridotta: colonne fisse, non mappatura interattiva)
- [x] Validazione riga per riga con serializer condivisi con la creazione manuale
- [ ] Elaborazione asincrona per file oltre una soglia dimensionale definita (implementazione ridotta: sempre sincrona, limite 5MB)
- [x] Report di importazione (righe ok / righe in errore) mostrato in UI
- [x] Strategia di deduplica definita (email) per l'entità Clienti
- [x] Template di importazione scaricabile per Clienti
- [x] Esportazione filtrata (rispetta la ricerca attiva) e completa, sincrona
- [x] Permessi RBAC verificati su import/export (Amministratore)
- [x] Log di audit per ogni operazione di massa
