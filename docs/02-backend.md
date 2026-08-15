# Backend — Architettura, Autenticazione, Database, Sicurezza

## Framework principale

**Python + Django + Django REST Framework (DRF)**

Perché questa combinazione per un gestionale:
- Django è "batteries included": ORM, sistema di migrazioni, autenticazione di base e, soprattutto, un **pannello di amministrazione generato automaticamente** (Django Admin) che copre gran parte delle esigenze CRUD interne quasi senza scrivere codice — utile sia come strumento di lavoro durante lo sviluppo sia come interfaccia di backup per l'amministratore
- Django REST Framework aggiunge sopra Django tutto il necessario per esporre API REST: serializzatori, autenticazione, permessi, viewset che riducono il codice ripetitivo
- Struttura "a app" che si presta bene a organizzare i moduli di un gestionale (app `users`, app `anagrafiche`, app `prenotazioni`...)
- Ecosistema maturo, stabile, ampiamente usato in produzione

### Alternative valide

| Framework | Quando preferirlo |
|---|---|
| **FastAPI** | Approccio più leggero e asincrono fin dall'inizio, meno "struttura imposta"; richiede di assemblare a parte ORM (SQLAlchemy/SQLModel) e autenticazione, ma è più veloce su carichi concorrenti elevati e genera documentazione OpenAPI automatica |
| Node.js + NestJS | Se si preferisce restare nello stesso linguaggio del frontend (TypeScript) per condividere tipi e validazioni |
| Express / Flask | Progetti piccoli, massima libertà/minimalismo |

Per un gestionale come questo — molte entità, CRUD, ruoli, pannello di amministrazione — **Django + DRF resta la scelta con meno attrito**: le convenzioni imposte tolgono decisioni da prendere una per una, e il pannello admin è un acceleratore concreto in fase di sviluppo e test.

## Database

**PostgreSQL**: relazionale, transazionale (ACID), adatto ai dati fortemente strutturati e collegati tipici di un gestionale (utenti↔ruoli, prenotazioni↔clienti↔servizi).

### ORM
- **Django ORM** — incluso in Django, non va scelto separatamente; migrazioni gestite con `python manage.py makemigrations` / `migrate`
- Se si passasse a FastAPI: **SQLAlchemy 2.0** (async) o **SQLModel** (più vicino a Pydantic, più semplice da iniziare)

### Schema di partenza generico (adattabile)

Le stesse entità di base viste finora, come modelli Django (`models.py`):

- `User` — Django fornisce già un modello utente base (`AbstractUser`), da estendere con i campi necessari
- `Role` / `Permission` — Django include già un sistema di permessi (`django.contrib.auth.models.Group` e `Permission`); per un RBAC più su misura restano comunque definibili modelli propri
- `Organization` — presente solo se serve multi-tenancy
- `EntitaGenerica` — placeholder da rinominare/duplicare in base al settore
- `AuditLog` — id, user, azione, entità coinvolta, timestamp, dettagli (`JSONField`, nativo con Postgres)
- `Settings` — chiave/valore per configurazioni

## Autenticazione

- **djangorestframework-simplejwt** — libreria di riferimento per JWT (access + refresh) sopra DRF, copre la maggior parte dei casi senza scrivere la logica a mano
- Preferire **RS256** a **HS256** se più servizi devono verificare i token
- **Mai** salvare i token in `localStorage`/`sessionStorage`: preferire cookie `httpOnly` + `Secure` + `SameSite`
- Hashing password: Django usa **PBKDF2** di default (già sicuro); **Argon2** disponibile come opzione (`Argon2PasswordHasher`) se si vuole allinearsi allo standard più recente
- **OAuth2/social login**: **django-allauth**
- **2FA (TOTP)**: **django-otp** o **django-two-factor-auth**

## Autorizzazione

- **RBAC**: Django/DRF offrono permessi a livello di modello e di vista (`permission_classes` nei viewset DRF); per permessi più granulari (es. "un operatore modifica solo le proprie prenotazioni") si può usare **django-guardian** (permessi per singolo oggetto) o logica custom nei serializzatori/viewset

## Sicurezza

Checklist minima — la sostanza non cambia rispetto a un backend Node, cambiano solo gli strumenti:

- **HTTPS obbligatorio** in ogni ambiente
- Django include già protezioni di base (CSRF, XSS, clickjacking) se non disattivate; **django-cors-headers** per CORS
- **Rate limiting**: `django-ratelimit` o il throttling integrato di DRF (`DEFAULT_THROTTLE_CLASSES`)
- **Validazione input**: i serializer DRF validano automaticamente in base ai campi/tipi dichiarati
- **Gestione segreti**: variabili d'ambiente (`django-environ`), mai in repo
- **SQL Injection**: mitigato dall'uso dell'ORM Django con query parametrizzate
- **Audit trail**: loggare azioni sensibili nel modello `AuditLog`
- **Backup automatici e testati** del database
- **Dipendenze**: `pip-audit` o Dependabot per la scansione delle vulnerabilità

## Design delle API

- **REST** versionato (`/api/v1/...`) tramite Router/ViewSet di DRF
- Documentazione automatica con **drf-spectacular** (schema OpenAPI/Swagger generato da serializer e viewset esistenti)

## Servizi di supporto

- **Redis**: cache (`django-redis`), broker per task asincroni
- **Celery** (con Redis come broker): equivalente Python di BullMQ — code per task asincroni come invio email, generazione PDF/report, elaborazioni pesanti
- **Storage file compatibile S3**: **django-storages** con backend S3, per documenti/allegati
- **Django Channels** (opzionale) se serve WebSocket per notifiche in tempo reale

## Testing
- **pytest** + **pytest-django** — developer experience più moderna del test runner integrato di Django
- **factory_boy** per generare dati di test in modo pulito

## Struttura cartelle proposta (Django, per app/dominio)

```
backend/
├── config/                 # settings, urls, wsgi/asgi (il "progetto" Django)
├── apps/
│   ├── users/
│   ├── roles/
│   ├── entita_generica/    # da rinominare/duplicare per settore
│   ├── notifiche/
│   ├── audit_log/
│   └── settings_app/
├── common/
│   ├── permissions.py
│   ├── pagination.py
│   └── exceptions.py
├── manage.py
└── requirements.txt
```
