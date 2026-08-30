# Changelog

Tutte le modifiche significative al progetto sono documentate in questo file.
Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e
il versionamento segue [Semantic Versioning](https://semver.org/lang/it/).

---

## [1.0.0] — 2026-08-28

Prima versione completa e pronta per il deploy in produzione.

### Aggiunto

**Backend (Django 5 + DRF)**

- Autenticazione JWT via cookie `httpOnly` con CSRF custom (niente `localStorage`)
- RBAC a 3 ruoli: Amministratore, Operatore, Cliente
- Catalogo Servizi con filtri per categoria e ricerca full-text
- Gestione Operatori con disponibilità settimanali configurabili
- Anagrafica Clienti con note preferenze riservate allo staff + supporto clienti ospiti (senza account)
- Prenotazioni con anti-doppia-prenotazione a livello di database (PostgreSQL `ExclusionConstraint` + `btree_gist`)
- Calcolo slot liberi in tempo reale (disponibilità − prenotazioni esistenti − buffer configurabile)
- Pagamenti e presenze: `stato_pagamento` / `stato_presenza` con tracciamento no-show automatico
- Politica no-show: blocco automatico alla soglia configurabile + sblocco manuale Amministratore
- Import in blocco Clienti da CSV/Excel (deduplica per email, report righe ok/errore/duplicati interni)
- Export CSV Clienti (rispetta i filtri attivi)
- Dashboard KPI per staff (prenotazioni oggi/settimana, tasso occupazione, fatturato, no-show)
- Dashboard guadagni dettagliata per Amministratore (per servizio, per operatore, top clienti, clienti vicini al blocco)
- Modulo Notifiche: in-app + email (conferma, cancellazione da staff, promemoria 24h, soglia no-show, alert admin)
- Push notifications VAPID end-to-end (PushSubscription model, endpoint subscribe, handler SW)
- Task Celery `invia_promemoria_prenotazioni` schedulato ogni 15 minuti via Celery Beat
- API Impostazioni (soglia no-show, buffer, preavviso cancellazione, intervallo slot) — solo Amministratore
- Endpoint `/health/` (django-health-check) per Docker healthcheck e provider di hosting
- Sicurezza produzione: `SECURE_HSTS_*`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `X_FRAME_OPTIONS`
- Sentry SDK (attivato solo in produzione con `SENTRY_DSN` configurato)
- AuditLog su: import clienti, export clienti, blocco/sblocco no-show
- `generate_vapid_keys` management command
- `populate_db` management command (101 prenotazioni, 3 mesi di storia, scenario realistico)
- `seed_demo_data` management command (setup minimo post-deploy)

**Frontend (React 19 + Vite + TypeScript)**

- Login con JWT cookie, protezione rotte, reindirizzamento automatico
- Sidebar con voci filtrate per ruolo (RoleGuard lato UI)
- Dashboard differenziata: KPI+Guadagni per staff, prossimo appuntamento per cliente
- Catalogo Servizi con CRUD completo (Amministratore) e sola lettura (Cliente/Operatore)
- Gestione Operatori (Amministratore)
- Anagrafica Clienti con ricerca, import CSV/Excel (modale + report), export CSV
- Pagina Prenota self-service: selezione servizio → operatore → slot liberi → conferma
- Le mie prenotazioni: lista con cancellazione (dentro i termini di preavviso)
- Gestione prenotazioni staff: presenza, pagamento inline, cancellazione override
- Utenti e ruoli: CRUD utenti + assegnazione ruoli (Amministratore)
- Impostazioni: tabella inline editabile (Amministratore)
- NotificationBell nell'header con badge non lette (polling 60s), dropdown, mark-as-read
- PushPrompt contestuale per attivare le notifiche push
- UpdatePrompt non invasivo per gli aggiornamenti del service worker
- InstallButton per l'installazione PWA via `beforeinstallprompt`
- OfflineBanner (stato rete in tempo reale)
- DataTable generico con sorting, paginazione lato server, azioni per riga
- FormModal generico guidato da schema Zod
- ConfirmDialog riutilizzabile
- Toast di feedback (successo/errore)

**PWA**

- Web App Manifest con icone 192/512/maskable on-brand
- Service worker custom (`injectManifest`): precache, `StaleWhileRevalidate` catalogo, `NetworkFirst` dati critici, handler `push`, handler `notificationclick`
- `registerType: 'prompt'` — aggiornamento su conferma esplicita, non silenzioso

**Infrastruttura**

- Docker Compose locale: Postgres 16, Redis 7, backend, celery-worker, celery-beat, frontend, adminer
- Dockerfile multi-stage (development / production) per backend e frontend
- `railway.json` per deploy Railway
- `_headers` + `_redirects` Cloudflare Pages (SPA fallback, security headers, `Service-Worker-Allowed`)
- CI GitHub Actions: lint, format, pip-audit, npm audit, pytest, tsc, build, migrate check
- CD GitHub Actions: deploy automatico su push a `main` (Railway + Cloudflare Pages)
- 3 test file Playwright E2E (auth, prenotazione, notifiche+impostazioni)

### Note

- Python 3.12 usato nell'ambiente di sviluppo (Python 3.13 nei docs ma non disponibile nei repository Ubuntu durante la ricostruzione dell'ambiente); nessun impatto funzionale
- Elaborazione import CSV sincrona (limite 5MB): appropriata per i volumi di un singolo salone
- Push notifications richiede configurazione VAPID (`python manage.py generate_vapid_keys`)
- Coda offline IndexedDB non implementata: azioni offline vengono segnalate (banner) ma non messe in coda per la sincronizzazione

---

## [0.4.0] — 2026-08-27 (interno)

- Modulo Notifiche completo (in-app + email + push)
- Impostazioni UI
- Celery Beat scheduling
- Playwright E2E

## [0.3.0] — 2026-08-22 (interno)

- PWA: manifest, service worker, install/update/offline

## [0.2.0] — 2026-08-15 (interno)

- Import/export Clienti
- Dashboard guadagni Amministratore

## [0.1.0] — 2026-08-11 (interno)

- Setup completo: autenticazione, RBAC, CRUD Servizi/Operatori/Clienti/Prenotazioni
- Anti-doppia-prenotazione DB, politica no-show, pagamenti/presenze
- Dashboard KPI staff, flusso prenotazione cliente
