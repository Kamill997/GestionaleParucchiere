# Docker e CI/CD di Base

## Perché containerizzare fin da subito

Anche per un progetto didattico o un MVP, avviare Postgres, Redis, backend e frontend tutti insieme con un comando solo evita il classico problema "sul mio computer funziona": ogni collaboratore (o il proprio io futuro, mesi dopo) riparte da un ambiente identico.

## docker-compose.yml (sviluppo locale)

Vedi `docker-compose.yml` nella root del repository. Rispetto a uno stack Node, si aggiunge `celery-worker`: il processo separato che esegue i task asincroni (invio email, generazione report, promemoria prenotazioni) descritti negli altri file. `adminer` è un client DB via browser, comodo in sviluppo (`http://localhost:8080`); da rimuovere in produzione.

## Dockerfile — backend (Django, multi-stage)

A differenza di un backend Node, non serve uno stage di build separato (Python è interpretato): lo stage `production` installa le dipendenze e serve l'app con **Gunicorn** invece del server di sviluppo di Django. Vedi `backend/Dockerfile`.

## Dockerfile — frontend (Vite + React, multi-stage)

Vedi `frontend/Dockerfile` e `frontend/nginx.conf` (necessario perché il routing di React Router funzioni anche dopo il refresh della pagina).

## .env.example

```
# Database
DATABASE_URL=postgresql://gestionale:gestionale@localhost:5432/gestionale

# Redis
REDIS_URL=redis://localhost:6379

# Django
DJANGO_SECRET_KEY=cambia-questo-con-un-segreto-forte-e-casuale
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# JWT (djangorestframework-simplejwt)
JWT_ACCESS_EXPIRATION_MINUTES=15
JWT_REFRESH_EXPIRATION_DAYS=30

# Frontend
VITE_API_URL=http://localhost:8000/api/v1

# Storage compatibile S3 (opzionale)
S3_ENDPOINT=
S3_BUCKET=
S3_ACCESS_KEY=
S3_SECRET_KEY=
```

`.env.example` va committato nel repository (senza valori reali); il file `.env` effettivo resta sempre in `.gitignore`.

## Sviluppo vs produzione

- **Sviluppo**: `docker-compose.yml` con stage `development`, codice montato come volume, `runserver` con reload automatico
- **Produzione**: build con stage `production` (`docker build --target production`), nessun codice sorgente montato, servito da Gunicorn dietro un reverse proxy (nginx o quello del provider di hosting)

## Healthcheck applicativo

- **django-health-check** espone un endpoint `/health` che verifica DB, cache/Redis e altri servizi collegati — equivalente Python di `@nestjs/terminus`, utile sia per gli healthcheck di Docker sia per il monitoraggio in produzione

## CI — GitHub Actions di base

Vedi `.github/workflows/ci.yml`. **ruff** è oggi il linter/formatter Python più veloce e diffuso, equivalente a ESLint+Prettier lato Node.

## CD — cenni al deploy

Lo step di deploy vero e proprio dipende dall'hosting scelto (vedi `09-hosting-e-dominio.md`), ma il pattern generale è:

1. Un secondo workflow (es. `.github/workflows/deploy.yml`), attivato solo su push a `main` e solo se la CI è passata
2. Costruzione dell'immagine Docker con lo stage `production`
3. Push dell'immagine a un registry (es. GitHub Container Registry) oppure deploy diretto tramite la CLI/azione ufficiale del provider scelto (Railway, Render...)
4. Su VPS con Docker Compose: uno step che si connette via SSH ed esegue `docker compose pull && docker compose up -d`

## Checklist

- [x] `docker compose up` avvia l'intero ambiente (DB, cache, backend, worker, **beat scheduler**, frontend) con un solo comando
- [x] `.env.example` presente e aggiornato, `.env` reale mai committato
- [x] Dockerfile con stage separati per sviluppo e produzione
- [x] Endpoint di healthcheck applicativo `/health/` funzionante
- [x] Pipeline CI verde su lint, test e build per entrambi i progetti
- [x] Pipeline di deploy (`deploy.yml`) scritta per Railway (backend) + Cloudflare Pages (frontend)
- [ ] Pipeline di deploy testata end-to-end verso l'ambiente di staging (da fare dopo la configurazione dei secret su GitHub)
