# Stato avanzamento — Gestionale Salone di Parrucchiere

_Snapshot aggiornato dopo la ricostruzione completa dell'ambiente da zero
(sandbox di sviluppo riavviato, nessuno zip fisico raggiungibile in quella
sessione — ricostruzione fatta a partire dal codice sorgente disponibile nel
contesto di lavoro) e il completamento di due moduli._

## Obiettivo di questa sessione — COMPLETATO

1. **`07-import-export-dati.md`** per Clienti — backend + frontend, testato.
2. **`08-pagamenti.md`**, ultimo pezzo del checklist — breakdown guadagni
   per servizio/operatore/cliente + elenco clienti vicini al blocco no-show,
   backend + frontend, testato.

Entrambi erano stati identificati come gap reali durante l'audit iniziale di
questa sessione (non solo dal riepilogo scritto, ma confrontando riga per
riga il codice reale con `docs/07-import-export-dati.md` e `docs/08-pagamenti.md`).

## Verifica ambiente ricostruito — fatta prima di scrivere codice nuovo

Come da procedura ("Prossimi 3 passi" della sessione precedente):

1. Codice sorgente riscritto su disco file per file dal contesto disponibile
2. Postgres 16 + Redis 7 installati e avviati, DB/utente `gestionale` creati,
   estensione `btree_gist` abilitata
3. `pytest` → **79/79 verdi** (uguale all'ultimo commit dichiarato) PRIMA di
   toccare qualunque riga di codice nuova
4. `npm install` + `vitest run` → **5/5 verdi** (uguale all'ultimo commit dichiarato)

Solo dopo questa doppia conferma si è proceduto con le modifiche.

## Lavoro di questa sessione (dettaglio)

### Import/export Clienti

- `backend/apps/clienti/import_export.py` (nuovo): `genera_template_csv()`,
  `importa_clienti()` (dedup per email via `ClienteSerializer` riusato,
  segnala duplicati interni), `esporta_clienti_csv()`
- `backend/apps/clienti/views.py`: 3 nuove action (`template-import/`,
  `importa/`, `esporta/`), tutte Amministratore-only; `AuditLog` importato
  correttamente fin dall'inizio (un tentativo precedente, mai committato,
  aveva lasciato questo import mancante — evitato qui)
- `backend/requirements.txt`: aggiunte `pandas>=2.2`, `openpyxl>=3.1`
- `backend/apps/clienti/test_import_export.py` (nuovo): 18 test
- `frontend/src/features/clienti/api.ts`, `hooks.ts`: funzioni/hook per
  template/import/export
- `frontend/src/features/clienti/ImportClientiDialog.tsx` (nuovo): modale
  upload + report (creati/aggiornati/errori/duplicati interni)
- `frontend/src/features/clienti/ClientiPage.tsx`: pulsanti Importa/Esporta
  (Amministratore-only via `RoleGuard`)
- `frontend/src/lib/api.ts`: `apiFetch` ora non forza `Content-Type:
  application/json` quando il body è `FormData` (bug che avrebbe rotto
  l'upload multipart — trovato e corretto durante l'implementazione, non
  dopo)
- `frontend/src/features/clienti/ClientiPage.test.tsx` (nuovo, la pagina non
  aveva test prima): 3 test (visibilità pulsanti per ruolo, flusso di
  import end-to-end con file mock)

### Dashboard guadagni (completamento `08-pagamenti.md`)

- `backend/apps/prenotazioni/services.py`: nuova `calcola_report_guadagni()`
  — per_servizio/per_operatore (ultimi 7 giorni, solo pagate), top_clienti
  (storico completo, primi 10), clienti_vicini_al_blocco (contatore ≥
  soglia-1, non ancora bloccati)
- `backend/apps/prenotazioni/serializers.py` + `views.py` + `urls.py`:
  `ReportGuadagniView` su `dashboard/report-guadagni/`, **riservata ad
  Amministratore** (non Operatore — i docs dicono esplicitamente "lato
  Amministratore" per questa sezione, a differenza del KPI generale)
- `backend/apps/prenotazioni/test_report_guadagni.py` (nuovo): 9 test
- `frontend/src/features/dashboard/hooks.ts`: nuovo `useReportGuadagni()`
- `frontend/src/features/dashboard/GuadagniSection.tsx` (nuovo) +
  `DashboardPage.tsx`: sezione Guadagni sotto la griglia KPI, visibile solo
  ad Amministratore

## Stato generale del progetto

**Fasi 1-4 complete** (Fase 4 ora davvero completa, import/export incluso).
`08-pagamenti.md` ora completo tranne l'email automatica di avviso no-show
(richiede il modulo Notifiche, non costruito).

Riepilogo per fase/modulo, vedi anche `README.md`:

- Fase 1 — scaffolding Django+DRF / Vite+React+TS, Docker, CI
- Fase 2 — auth JWT cookie httpOnly + CSRF custom, RBAC (User/Role/Permission)
- Fase 3 — layout, routing, login reale, design system
- Fase 4 — Servizi/Operatori/Clienti/Prenotazioni (anti-doppia-prenotazione
  DB via `ExclusionConstraint`+`btree_gist`), CRUD generico riusabile,
  dashboard KPI, gestione utenti/ruoli, flusso prenotazione self-service
  cliente + vista staff, **import/export Clienti**
- `08-pagamenti.md` — pagamento/presenza/no-show, **dashboard guadagni completa**

**106 test backend + 12 test frontend, tutti verdi.**

## Fase 5 — PWA (nucleo tecnico), aggiunta nello stesso filo di sessione

Dopo i due moduli sopra, proseguito naturalmente con `04-pwa-checklist.md`
(prossimo passo indicato a fine sessione precedente):

- `vite-plugin-pwa` configurato in `vite.config.ts`: manifest (icone
  192/512/maskable generate on-brand in `frontend/public/icons/` via
  Pillow, dato che non esisteva un asset icona pronto), `lang: 'it'`
  (di default sarebbe finito 'en', corretto)
- Caching API secondo la tabella dei docs: `StaleWhileRevalidate` per
  catalogo, `NetworkFirst` per dati critici, nessuna regola per le
  mutazioni (comportamento di default Workbox: le route runtimeCaching
  intercettano solo GET)
- **Decisione deliberata**: `registerType: 'prompt'`, non `'autoUpdate'`
  come lo snippet di esempio nel file docs — la prosa subito sotto quello
  snippet chiede esplicitamente un banner non invasivo invece di un reload
  forzato; seguito il requisito scritto, non l'esempio di codice
- `UpdatePrompt.tsx`, `InstallButton.tsx` (via `beforeinstallprompt`),
  `OfflineBanner.tsx` (stato rete) — nuovi componenti, montati in `App.tsx`
  e `Header.tsx`
- Verificato con build reale (`vite build`): `dist/sw.js` +
  `manifest.webmanifest` generati correttamente, 33 entry precache
- 4 nuovi test frontend (12 totali)
- **Non fatto, dichiarato esplicitamente**: coda offline IndexedDB/Dexie
  (solo il banner di stato, non la sincronizzazione), notifiche push
  (serve il modulo Notifiche), verifica reale su dispositivi e audit
  Lighthouse (non eseguibili in questo sandbox: niente HTTPS reale, niente
  dispositivi fisici)

## Problemi aperti / rischi noti (invariati rispetto a prima)

- Il sandbox può resettarsi senza preavviso: **confermato di nuovo in questa
  sessione** (zip della sessione precedente non raggiungibile, ricostruzione
  fatta dal contesto disponibile). La ricostruzione ha funzionato perché il
  codice completo era comunque disponibile nel contesto di lavoro — non
  sempre sarà così: **committare su un repository Git reale (non solo
  produrre uno zip di consegna) resta la protezione più solida.**
- Postgres/Redis non sopravvivono tra le chiamate bash separate in questo
  ambiente: vanno riavviati a inizio di ogni gruppo di comandi
  (`service postgresql start && service redis-server start && sleep 2`).
- Python 3.13 (da `docs/02-backend.md`) non disponibile nei repository apt
  raggiungibili dall'ambiente di ricostruzione più recente: usato Python
  3.12 come sostituto pragmatico (nessuna differenza di comportamento per
  Django 5 + DRF), dichiarato esplicitamente invece di essere nascosto.
- Nessun modulo Notifiche: email automatica no-show, promemoria prenotazioni,
  conferme — tutto ancora da costruire.
- Import/export Clienti: elaborazione sincrona, limite 5MB — va bene per un
  singolo salone, non scala a dataset grandi (semplificazione deliberata).

## Modulo Notifiche — aggiunto nello stesso filo di sessione

Terzo modulo dopo import/export e dashboard guadagni, prima candidatura
indicata a fine giro PWA (sblocca l'ultimo punto aperto di 08-pagamenti.md
e le notifiche di esempio-settore-parrucchiere.md):

- `apps/notifiche/` (models/services/serializers/views/urls/admin) da zero:
  modello `Notifica`, `crea_notifica()`/`notifica_cliente()` (gestisce
  anche i clienti ospiti senza account, solo email diretta)
  /`notifica_amministratori()`, backend email a console in sviluppo
- Collegato a: creazione prenotazione (conferma cliente + avviso operatore),
  cancellazione da staff (avviso cliente, non a se stessi se e' il cliente
  a cancellare), soglia no-show raggiunta (avviso cliente + admin —
  **completa l'ultimo punto di 08-pagamenti.md**), sblocco cliente (avviso admin)
- `apps/prenotazioni/tasks.py`: task Celery per il promemoria 24h, logica
  scritta e testata, schedulazione Celery Beat non configurata (dichiarato)
- Frontend: `NotificationBell.tsx` nell'Header, badge non lette con polling
- 16 nuovi test backend + 2 frontend

**122 test backend + 14 test frontend, tutti verdi.**

## Prossimi passi

1. **Notifiche push** (VAPID/pywebpush): il modulo Notifiche e il nucleo
   PWA esistono entrambi già, manca solo il collegamento vero e proprio
   (chiavi VAPID, `PushSubscription` model, handler `push` nel service worker).
2. **Celery Beat**: schedulare `invia_promemoria_prenotazioni` (già scritto
   e testato) e aggiungere il servizio in `docker-compose.yml`.
3. **PWA, coda offline**: IndexedDB/Dexie + Background Sync per le azioni
   compiute offline (oggi solo segnalate con un banner, non messe in coda).
4. **Impostazioni (UI)**: il backend (`Impostazione`/`get_int()`) esiste già
   ed è usato attivamente; manca solo una pagina per modificarlo senza
   passare da Django Admin.
5. Committare su un repository Git reale e/o GitHub, non solo produrre uno
   zip di consegna — riduce concretamente il rischio di un altro reset che
   perda lavoro non salvato altrove.

## Fasi 6-9 + Celery Beat + Impostazioni UI — stesso filo di sessione

Dopo il modulo Notifiche, completati i passi di maturità rimanenti:

### Impostazioni UI (Fase 4 completa)
- `settings_app/serializers.py`, `views.py`, `urls.py`: endpoint
  `impostazioni/` (list+update, Amministratore-only; validazione intera
  non-negativa; lazy get_or_create di tutte le chiavi note alla prima
  apertura)
- `features/impostazioni/`: `ImpostazioniPage.tsx` con editing inline
  (click → input inline → Invio/Esc)
- Rotta `/impostazioni` + voce sidebar
- 6 nuovi test backend

### Celery Beat (schedulazione task promemoria)
- `CELERY_BEAT_SCHEDULE` in `settings.py`: `invia_promemoria_prenotazioni`
  ogni 15 minuti via `crontab`
- Servizio `celery-beat` in `docker-compose.yml` con schedule file
  persistente su volume dedicato `celerybeat_data`

### Hardening sicurezza (Fase 6)
- `SECURE_HSTS_*`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`,
  `X_FRAME_OPTIONS`, `SECURE_SSL_REDIRECT` — tutti condizionati a
  `not DEBUG`, non rompono sviluppo locale

### Health check endpoint (Fase 9)
- `django-health-check` v4 installato, endpoint `/health/` in `urls.py`
- Healthcheck aggiunto al servizio `backend` in `docker-compose.yml`
- Nota tecnica risolta: v4 non ha i sottomoduli `db`/`cache`/`storage`
  della documentazione online (rimandava a v3); usata `HealthCheckView`
  direttamente

### CI/CD (Fasi 7-8)
- `ci.yml` aggiornato: aggiunto Redis come servizio, `migrate` prima di
  `migrate --check`, `npx tsc -b` esplicito nel job frontend, build
  completa in CI (verifica sw.js + manifest PWA ad ogni push)
- `deploy.yml` nuovo: Cloudflare Pages (frontend via wrangler-action) +
  Railway (backend via railway-cli), trigger su push a main

**131 test backend + 14 test frontend, tutti verdi.**

## Prossimi passi

1. **Primo deploy reale**: configurare i secret GitHub (`RAILWAY_TOKEN`,
   `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `VITE_API_URL`) e
   fare il primo push a main. Tutto il codice di deploy è già scritto.
2. **Playwright E2E**: aggiungere test end-to-end sui flussi critici
   (login, prenotazione, no-show) — l'unico pezzo di testing ancora mancante.
3. **Sentry**: aggiungere `sentry-sdk` a `requirements.txt` e
   `SENTRY_DSN` a `.env.example` dopo il primo deploy.
4. **Notifiche push** (VAPID): il modulo Notifiche e la PWA esistono;
   manca solo il collegamento (`PushSubscription` model, endpoint
   `/push-subscribe/`, handler nel service worker).
5. **pip-audit / npm audit**: scansione dipendenze da aggiungere alla CI
   (Fase 6 ancora scoperta).
