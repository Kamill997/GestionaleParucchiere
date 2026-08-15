# Passaggi Esecutivi — Roadmap di Sviluppo

Roadmap organizzata in fasi. Ogni fase presuppone il completamento (almeno parziale) della precedente.

## Fase 0 — Analisi e Pianificazione
- [ ] Definire il settore target e la terminologia di dominio
- [ ] Individuare le entità principali da gestire e le relazioni tra loro (bozza schema ER)
- [ ] Definire i ruoli utente e i permessi associati
- [ ] Verificare eventuali vincoli normativi/di compliance del settore (GDPR sempre valido in UE; normative verticali se presenti)
- [ ] Definire i documenti/report che il sistema dovrà produrre

## Fase 1 — Setup del Progetto
- [ ] Creazione repository (monorepo con workspace, es. pnpm/Turborepo, oppure due repo separati FE/BE)
- [ ] Configurazione ambiente di sviluppo: Node.js LTS per il frontend, Python 3.13 (venv) per il backend
- [ ] Configurazione linting/formatting: ESLint + Prettier (frontend), ruff (backend)
- [ ] Setup CI iniziale (lint + test ad ogni push/PR)
- [ ] Convenzioni di commit (es. Conventional Commits) e di branching (es. trunk-based o Git Flow semplificato)
- [ ] Ambiente Docker locale funzionante: `docker compose up` avvia DB, cache, backend e frontend (vedi `06-docker-e-cicd.md`)

## Fase 2 — Fondamenta Backend
- [ ] Setup progetto Django + Django REST Framework (o framework scelto)
- [ ] Connessione al database, primi modelli Django
- [ ] Prime migrazioni: `User`, `Role`, `Permission`, `AuditLog`
- [ ] Modulo di autenticazione (registrazione, login, refresh token)
- [ ] Guard RBAC funzionanti su almeno un endpoint protetto
- [ ] Documentazione API di base (Swagger) raggiungibile

## Fase 3 — Fondamenta Frontend
- [ ] Setup Vite + React + TypeScript
- [ ] Routing di base e layout (sidebar, header, area di contenuto)
- [ ] Integrazione autenticazione (login funzionante contro il backend, gestione token, rotte protette)
- [ ] Design system minimo: bottoni, input, tabella, modale

## Fase 4 — Sviluppo Feature Core
- [ ] CRUD generico riusabile (tabella + form) collegato al backend
- [ ] Dashboard con almeno 2-3 KPI reali
- [ ] Gestione Utenti & Ruoli completa lato UI
- [ ] Primo modulo specifico di settore (l'entità principale del dominio)
- [ ] Modulo di importazione/esportazione dati in blocco per l'entità principale (vedi `07-import-export-dati.md`)
- [ ] Tracciamento pagamento/presenza e politica no-show (vedi `08-pagamenti.md`)

## Fase 5 — Implementazione PWA
- [ ] Integrazione `vite-plugin-pwa`, manifest completo con icone
- [ ] Service worker con strategie di caching definite (vedi `04-pwa-checklist.md`)
- [ ] Test del comportamento offline
- [ ] Test di installabilità su almeno due dispositivi/browser

## Fase 6 — Sicurezza e Hardening
- [ ] Rate limiting su endpoint sensibili
- [ ] Verifica configurazione CORS/Helmet
- [ ] Scansione dipendenze (`npm audit` per il frontend, `pip-audit` per il backend)
- [ ] Revisione gestione segreti (nessun secret committato nel repository)
- [ ] Test dei permessi (un utente non deve poter accedere a dati/azioni fuori dal proprio ruolo)

## Fase 7 — Testing
- [ ] Unit test backend (servizi, guard)
- [ ] Test di integrazione sugli endpoint principali
- [ ] Test di componente frontend sui componenti condivisi (DataTable, FormModal...)
- [ ] Test end-to-end sui flussi critici (login, creazione/modifica entità principale)

## Fase 8 — Deploy
- [ ] Scelta hosting frontend (es. Cloudflare Pages/Netlify/Vercel — vedi `09-hosting-e-dominio.md`)
- [ ] Scelta hosting backend + database (es. Railway/Render, oppure VPS con Docker Compose)
- [ ] Variabili d'ambiente configurate per ogni ambiente (dev/staging/prod)
- [ ] Pipeline CI/CD di deploy automatico
- [ ] Certificato HTTPS attivo ovunque

## Fase 9 — Monitoraggio e Manutenzione
- [ ] Error tracking (es. Sentry) collegato a frontend e backend
- [ ] Logging centralizzato lato backend
- [ ] Backup automatici del database verificati (non solo configurati: testare un ripristino reale)
- [ ] Piano di aggiornamento periodico delle dipendenze

## Checklist finale pre-lancio
- [ ] Audit Lighthouse (Performance, PWA, Accessibilità, Best Practice) tutti verdi o quasi
- [ ] Test di carico di base sugli endpoint più usati
- [ ] Verifica che i dati sensibili non compaiano nei log
- [ ] Documentazione minima per chi userà il gestionale (anche solo poche pagine)
