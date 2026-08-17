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

## Prossimi passi

1. **Modulo Notifiche**: sbloccherebbe sia l'email no-show di
   `08-pagamenti.md` sia le notifiche di conferma/promemoria di
   `esempio-settore-parrucchiere.md`, sia le notifiche push della PWA
   (nucleo tecnico già pronto, manca solo il backend VAPID/pywebpush).
2. **PWA, coda offline**: IndexedDB/Dexie + Background Sync per le azioni
   compiute offline (oggi solo segnalate con un banner, non messe in coda).
3. **Impostazioni (UI)**: il backend (`Impostazione`/`get_int()`) esiste già
   ed è usato attivamente; manca solo una pagina per modificarlo senza
   passare da Django Admin.
4. Committare su un repository Git reale e/o GitHub, non solo produrre uno
   zip di consegna — riduce concretamente il rischio di un altro reset che
   perda lavoro non salvato altrove.
