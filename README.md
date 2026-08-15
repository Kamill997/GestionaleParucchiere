# Gestionale Salone di Parrucchiere

PWA gestionale per un salone di parrucchiere/centro estetico: prenotazioni,
catalogo servizi, notifiche, gestione clienti/operatori, lato cliente e
amministratore.

Il progetto segue lo scheletro generico documentato in `docs/` (adattabile
ad altri settori) e il caso applicato in `docs/esempio-settore-parrucchiere.md`.

## Stack

- **Frontend**: React 19 (Vite, TypeScript), Tailwind CSS, React Router,
  TanStack Query, Zustand — vedi `docs/01-frontend.md`
- **Backend**: Python 3.12/3.13, Django 5 + Django REST Framework, PostgreSQL 16,
  Redis, Celery — vedi `docs/02-backend.md`
- **PWA**: `vite-plugin-pwa` (Fase 5, non ancora iniziata) — vedi `docs/04-pwa-checklist.md`

## Struttura

```
.
├── docs/                    # documentazione di riferimento (fonte di verità del progetto)
├── frontend/                 # Vite + React + TypeScript
├── backend/                  # Django + Django REST Framework
├── docker-compose.yml         # ambiente locale (Postgres, Redis, backend, worker, frontend)
├── .env.example               # variabili d'ambiente, copiare in .env
└── .github/workflows/ci.yml   # CI: lint + test per backend e frontend
```

## Avvio rapido (Docker)

```bash
cp .env.example .env      # e impostare un DJANGO_SECRET_KEY reale
docker compose up
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Documentazione API (Swagger): http://localhost:8000/api/docs/
- Adminer (client DB): http://localhost:8080

## Avvio rapido (senza Docker)

```bash
# Backend
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py runserver

# Frontend (in un altro terminale)
cd frontend
npm install
npm run dev
```

> **Nota Python**: i docs indicano Python 3.13; l'ambiente di sviluppo più
> recente in cui il progetto è stato ricostruito aveva solo Python 3.12
> disponibile nei repository raggiungibili. Django 5 + DRF funzionano
> identicamente su 3.12: nessun cambiamento di codice richiesto, solo
> annotato qui come deviazione dichiarata (stesso principio delle altre
> semplificazioni annotate in questo file).

Per accedere al Django Admin, creare un superuser (chiede email, non username):

```bash
cd backend && ./.venv/bin/python manage.py createsuperuser
```

## API disponibili

Tutte sotto `/api/v1/`, JWT in cookie httpOnly (non header `Authorization`):

| Endpoint | Metodo | Auth | Note |
|---|---|---|---|
| `auth/register/` | POST | pubblico | crea utente + record Cliente collegato, ruolo `Cliente` automatico |
| `auth/login/` | POST | pubblico | imposta cookie `access_token`/`refresh_token` |
| `auth/logout/` | POST | autenticato | invalida il refresh token, cancella i cookie |
| `auth/refresh/` | POST | cookie refresh | rinnova `access_token` |
| `auth/csrf/` | GET | pubblico | imposta il cookie `csrftoken` (chiamare all'avvio della SPA) |
| `auth/me/` | GET | autenticato | dati utente corrente |
| `admin/utenti/` | GET/POST/PATCH | ruolo `Amministratore` | gestione utenti/ruoli completa |
| `servizi/` | GET | autenticato | lettura per tutti; filtri `categoria`/`attivo`, ricerca |
| `servizi/` | POST/PUT/DELETE | ruolo `Amministratore` | gestione catalogo |
| `operatori/` | GET | autenticato | lettura per tutti |
| `operatori/` | POST/PUT/DELETE | ruolo `Amministratore` | gestione staff |
| `disponibilita/` | GET | autenticato | turni settimanali degli operatori |
| `disponibilita/` | POST/PUT/DELETE | ruolo `Amministratore` | gestione turni |
| `clienti/` | GET/POST/PATCH | autenticato | staff vede/gestisce tutti i clienti; un Cliente vede solo il proprio record |
| `clienti/{id}/sblocca/` | POST | ruolo `Amministratore` | rimuove il blocco no-show (il contatore resta) |
| `clienti/template-import/` | GET | ruolo `Amministratore` | CSV di esempio per l'import in blocco |
| `clienti/importa/` | POST (multipart) | ruolo `Amministratore` | import in blocco CSV/Excel, dedup per email |
| `clienti/esporta/` | GET | ruolo `Amministratore` | export CSV, rispetta `?search=` attivo |
| `slot-disponibili/` | GET | autenticato | `?operatore=&servizio=&data=YYYY-MM-DD` → slot liberi |
| `prenotazioni/` | GET/POST | autenticato | un Cliente vede/crea solo le proprie; un Operatore solo le proprie assegnate; Amministratore tutte |
| `prenotazioni/{id}/cancella/` | POST | autenticato | libera fino a 24h prima (configurabile); lo staff può sempre |
| `prenotazioni/{id}/segna-presenza/` | POST | staff | incrementa il no-show se assente |
| `dashboard/kpi/` | GET | staff | prenotazioni oggi/settimana, servizio top, occupazione, fatturato, tasso no-show |
| `dashboard/report-guadagni/` | GET | ruolo `Amministratore` | guadagni per servizio/operatore (7gg), top clienti (storico), clienti vicini al blocco |

Le richieste `POST`/`PUT`/`PATCH`/`DELETE` autenticate via cookie richiedono
l'header `X-CSRFToken`, tranne `login`. Tutto questo è già gestito da
`frontend/src/lib/api.ts` (`apiFetch`).

## Stato del progetto

**Fase 1 (Setup), Fase 2 (Autenticazione e ruoli), Fase 3 (Fondamenta frontend)**: complete.

**Fase 4 (Sviluppo Feature Core): completa.**

- [x] CRUD generico riusabile (DataTable/FormModal/RoleGuard/toast)
- [x] Dashboard con KPI reali (staff) + prossimo appuntamento (Cliente)
- [x] Gestione Utenti & Ruoli lato UI
- [x] Servizi/Operatori/Clienti/Prenotazioni, con anti-doppia-prenotazione a
      livello DB (`ExclusionConstraint` Postgres + `btree_gist`)
- [x] Flusso di prenotazione self-service lato Cliente (`/prenota`) + storico
      cancellabile (`/le-mie-prenotazioni`) + vista staff (`/gestione-prenotazioni`)
- [x] Pagamenti/presenze e politica no-show (`08-pagamenti.md`) — vedi sotto
- [x] **Import/export dati per Clienti (`07-import-export-dati.md`)** — vedi sotto

### Import/export Clienti (`07-import-export-dati.md`)

Scope volutamente ridotto rispetto ai docs generici (dichiarato esplicitamente,
non nascosto nel codice):

- **Elaborazione sincrona**, non Celery/async: i volumi realistici di un
  singolo salone sono piccoli
- **Colonne fisse da template** (`nome, email, telefono, note_preferenze`,
  esattamente i campi scrivibili di `ClienteSerializer`), non un mappatore
  interattivo di colonne libere

Implementazione:

- `backend/apps/clienti/import_export.py` — `genera_template_csv()`,
  `importa_clienti()` (valida riga per riga riusando `ClienteSerializer`,
  dedup per email: aggiorna se esiste altrimenti crea, segnala duplicati
  interni al file), `esporta_clienti_csv()`
- 3 nuove action su `ClienteViewSet`: `GET template-import/`,
  `POST importa/`, `GET esporta/` — tutte riservate ad Amministratore anche
  se la gestione clienti in sé è staff-wide (Amministratore + Operatore)
- Limite file 5MB, solo `.csv`/`.xlsx`; ogni import/export registra un
  evento in `AuditLog`
- Frontend: pulsanti Importa/Esporta su `ClientiPage` (visibili solo ad
  Amministratore via `RoleGuard`), modale di upload con report finale
  (`ImportClientiDialog`), link diretto di export che rispetta la ricerca
  attiva nella tabella
- 18 test backend dedicati (dedup, righe malformate, duplicati interni,
  estensione/dimensione file, permessi, audit log) + 3 test frontend
  (visibilità pulsanti per ruolo, flusso di import end-to-end)

> Nota storica: un tentativo precedente di questo stesso modulo era stato
> scritto ma perso in un reset del sandbox di sviluppo prima del commit (un
> `NameError` per `AuditLog` non importato in `views.py` era stato trovato e
> corretto in quel tentativo). In questa riscrittura l'import è stato incluso
> fin dall'inizio, evitando di ripetere lo stesso bug.

### Pagamenti, presenze e dashboard guadagni (`08-pagamenti.md`)

**Completo, incluso l'ultimo pezzo del checklist rimasto scoperto finora**
(la sola dashboard guadagni aggregata, senza i breakdown per cliente/servizio/operatore):

- [x] `stato_pagamento`/`importo`/`stato_presenza` su Prenotazione — solo staff può modificarli
- [x] Conteggio no-show su `Cliente`, soglia configurabile (default 3), blocco automatico, sblocco manuale (solo Amministratore)
- [x] Dashboard KPI: fatturato aggregato (7 giorni) e tasso no-show (`dashboard/kpi/`, staff-wide)
- [x] **Nuovo**: `apps/prenotazioni/services.calcola_report_guadagni()` — guadagni
      per servizio e per operatore (ultimi 7 giorni), top 10 clienti per
      fatturato storico, elenco clienti a un solo no-show dal blocco automatico
      (esclusi i già bloccati). Esposto su `dashboard/report-guadagni/`,
      **riservato ad Amministratore** (non Operatore: il titolo della sezione
      nei docs è esplicitamente "lato Amministratore", a differenza del KPI
      generale che resta staff-wide)
- [x] Frontend: sezione "Guadagni" su `DashboardPage`, visibile solo ad
      Amministratore, sotto la griglia KPI esistente (`GuadagniSection.tsx`)
- [x] 9 nuovi test backend (`test_report_guadagni.py`): aggregazioni corrette,
      esclusione prenotazioni non pagate/cancellate, ordinamento, permessi
- [ ] Email automatica di avviso al raggiungimento della soglia no-show —
      resta scoperta: richiede il modulo Notifiche (non ancora costruito,
      vedi sotto). L'evento viene comunque registrato in `AuditLog`.

### Cosa resta scoperto

- **Fase 5 (PWA)** — non iniziata: `vite-plugin-pwa`, manifest, service
  worker, test offline/installabilità
- **Modulo Notifiche** — non iniziato (solo stub): email no-show automatica,
  promemoria prenotazioni, conferme
- **Documenti & Allegati**, **Ricerca globale** — non iniziati
- **Reportistica PDF/Excel** oltre al CSV Clienti e ai report guadagni in-app
  — non iniziata come modulo dedicato
- **Impostazioni (UI)** — il modello `Impostazione`/`get_int()` esiste ed è
  usato attivamente (soglia no-show, buffer prenotazioni...), ma senza una
  pagina di gestione dedicata: si modifica via Django Admin
- **Fase 6-9** (Hardening formale, E2E, Deploy, Monitoraggio) — non iniziate

## Convenzioni

- **Commit**: [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`...)
- **Branching**: trunk-based semplificato — branch corti da `main`,
  merge tramite PR quando la CI è verde
- Un modulo/fase alla volta, con verifica funzionale prima di passare al successivo
  (vedi `docs/10-guida-vibe-coding.md`)

## Note operative sul reset dell'ambiente

Questa consegna è stata ricostruita da zero in un sandbox di sviluppo
completamente nuovo, a partire dal codice sorgente disponibile nel contesto
di lavoro (non da un file `.zip` fisico, non raggiungibile in quella
sessione). Verificato che la ricostruzione fosse fedele al commit precedente
prima di procedere: **79/79 test backend preesistenti verdi** e **5/5 test
frontend preesistenti verdi**, prima di aggiungere qualunque riga di codice
nuova. Il totale attuale è **106 test backend** e **8 test frontend**, tutti
verdi.
