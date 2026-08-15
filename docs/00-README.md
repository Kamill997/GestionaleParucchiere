# Scheletro Gestionale PWA — Guida Generale

> Set di documenti di riferimento per la progettazione e lo sviluppo di un'applicazione **gestionale** in forma di **Progressive Web App (PWA)**, pensato come base riutilizzabile e adattabile a settori diversi (retail, sanità, logistica, formazione, servizi professionali, produzione, ecc.).

L'idea centrale: l'80% dell'architettura (autenticazione, ruoli, CRUD, notifiche, reportistica, PWA) è identica in qualunque settore. Cambia solo il 20% legato al dominio specifico (le "anagrafiche" e i loro campi). Questo scheletro è pensato per separare nettamente le due cose.

## Struttura dei file

| File | Contenuto |
|---|---|
| `00-README.md` | Questa guida: indice e checklist di adattamento |
| `01-frontend.md` | Stack frontend (React + framework di supporto), librerie, struttura cartelle |
| `02-backend.md` | Stack backend, autenticazione, database, sicurezza |
| `03-componenti-e-workflow.md` | Moduli applicativi, ordine di sviluppo, esempi di adattamento per settore |
| `04-pwa-checklist.md` | Requisiti tecnici specifici PWA (manifest, service worker, offline, push) |
| `05-passaggi-esecutivi.md` | Roadmap operativa fase per fase, in formato checklist |
| `06-docker-e-cicd.md` | Containerizzazione Docker, ambiente locale, pipeline CI/CD |
| `07-import-export-dati.md` | Importazione/esportazione dati in blocco, migrazione da sistemi legacy |
| `08-pagamenti.md` | Tracciamento pagamento e presenza, politica no-show, dashboard guadagni |
| `09-hosting-e-dominio.md` | Dove hostare (gratis e a pagamento), dominio personale, costi indicativi |
| `10-guida-vibe-coding.md` | Come iniziare l'implementazione con un'IA agentica, prompt di esempio fase per fase |

## Esempi applicati a settori specifici

Oltre ai file di base (`00`-`07`), che restano generici e adattabili, questa raccolta può accogliere esempi già "compilati" per un settore specifico — utili come riferimento concreto o da presentare così come sono:

| File | Settore |
|---|---|
| `esempio-settore-parrucchiere.md` | Salone di parrucchiere/centro estetico: prenotazioni, catalogo servizi, notifiche, lato cliente e amministratore |

Nuovi esempi per altri settori possono seguire la stessa struttura: ruoli utente, entità di dominio, funzionalità lato utente/amministratore, logica di business specifica, schema dati, notifiche, cosa cambia e cosa resta invariato rispetto allo scheletro generico.

## Ordine di lettura consigliato

1. Questo README, per avere il quadro generale
2. `01-frontend.md` e `02-backend.md`, per fissare lo stack tecnologico
3. `06-docker-e-cicd.md`, per avere l'ambiente locale pronto prima di scrivere codice
4. `03-componenti-e-workflow.md`, per capire cosa costruire e in che ordine (`07-import-export-dati.md` e `08-pagamenti.md` quando si arriva ai moduli corrispondenti)
5. `04-pwa-checklist.md`, quando si arriva alla fase di implementazione PWA vera e propria
6. `05-passaggi-esecutivi.md`, da tenere aperto come checklist operativa durante tutto lo sviluppo
7. `10-guida-vibe-coding.md`, per impostare il flusso di lavoro con l'IA prima di iniziare a scrivere codice
8. `09-hosting-e-dominio.md`, quando si arriva alla fase di deploy

## Checklist di adattamento a un settore specifico

Prima di iniziare lo sviluppo su un nuovo settore, rispondere a queste domande — le risposte determinano cosa personalizzare nello scheletro:

1. **Dominio/settore**: quale settore? (retail, sanità, logistica, HR, formazione, studio professionale...)
2. **Entità principali**: quali sono gli "oggetti" centrali da gestire? (clienti, pazienti, studenti, prodotti, spedizioni, pratiche...)
3. **Ruoli utente**: quali ruoli esistono e cosa può fare ciascuno? (admin, manager, operatore, cliente esterno...)
4. **Normative/compliance**: vincoli normativi specifici? (GDPR è sempre valido in UE; possono aggiungersi normative di settore: sanitarie, finanziarie, contabili...)
5. **Reportistica**: che documenti servono? (fatture, referti, pagelle, bolle di trasporto, preventivi...)
6. **Integrazioni esterne**: fatturazione elettronica, gateway di pagamento, SPID/CIE, corrieri, sistemi di terze parti già in uso dal cliente?
7. **Multi-tenancy**: il gestionale serve una sola organizzazione o più organizzazioni distinte sulla stessa istanza?
8. **Lingue**: serve supporto multilingua?

Le risposte a queste domande incidono quasi solo sul modulo "Anagrafiche" descritto in `03-componenti-e-workflow.md`: il resto dello scheletro (auth, ruoli, notifiche, audit, PWA) resta stabile.

## Stack tecnologico di sintesi

| Livello | Scelta principale | Alternative valide |
|---|---|---|
| Frontend | React + Vite | Vue 3 + Vite, SvelteKit, Angular |
| Stato server | TanStack Query | SWR, RTK Query |
| Stato client | Zustand | Redux Toolkit, Jotai |
| Routing | React Router | TanStack Router |
| UI Kit | Tailwind CSS + shadcn/ui | MUI, Ant Design, Chakra UI |
| Backend | Python + Django + DRF | FastAPI, Node.js + NestJS, Laravel, Spring Boot |
| Database | PostgreSQL | MySQL, MongoDB (per dati non strutturati) |
| ORM | Django ORM | SQLAlchemy / SQLModel (con FastAPI) |
| Autenticazione | JWT via djangorestframework-simplejwt | Sessioni server-side, OAuth2/OIDC (django-allauth) |
| Cache / Code | Redis + Celery | — |
| Pagamenti | Tracciamento manuale (pagato/non pagato) | Stripe, se in futuro si vorrà un pagamento online |
| Containerizzazione | Docker + Docker Compose | — |
| CI/CD | GitHub Actions | GitLab CI, altri |
| Hosting frontend | Cloudflare Pages | Netlify, Vercel (piano gratuito solo non commerciale) |
| Hosting backend | Railway / Render / VPS + Docker | AWS / GCP / Azure |

Questa tabella riflette scelte correnti e ampiamente adottate al momento della stesura (metà 2026); vale comunque la pena, all'inizio di ogni nuovo progetto, una verifica rapida che non siano cambiati equilibri importanti nell'ecosistema.

## Come usare praticamente questo scheletro

- Copiare l'intera cartella di documenti nel repository del nuovo progetto (es. in una cartella `docs/`)
- Compilare la checklist di adattamento sopra come primo passo
- Usare `05-passaggi-esecutivi.md` come issue/board iniziale (ogni checkbox può diventare una task)
- Aggiornare i documenti man mano che si prendono decisioni definitive, così restano la fonte di verità del progetto e non solo un piano iniziale
