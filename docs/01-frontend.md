# Frontend — Stack e Architettura

## Framework principale

**React 18+ con Vite** come build tool (non Create React App, ormai superata e non più il punto di partenza consigliato).

Perché questa combinazione per un gestionale:
- Ecosistema maturo, con enorme disponibilità di librerie per tabelle, form e grafici — elementi centrali in qualunque gestionale
- Dev server istantaneo e build ottimizzate
- Ottimo supporto PWA tramite plugin dedicato (vedi sotto e `04-pwa-checklist.md`)

### Alternative valide

| Framework | Quando preferirlo |
|---|---|
| Vue 3 + Vite | Team con preferenza per sintassi più lineare, curva di apprendimento più dolce |
| SvelteKit | Progetti che privilegiano bundle minimi e performance estrema |
| Angular | Team enterprise già strutturati su Angular, progetti molto grandi con convenzioni rigide già consolidate |

## Librerie principali consigliate

### Routing
- **React Router** — soluzione più diffusa e "sicura", supporto nested routes (utile per layout con sidebar + sezioni)
- **TanStack Router** — alternativa più recente, type-safe end-to-end; da valutare se il team è già nell'ecosistema TanStack (vedi sotto) e vuole route fortemente tipizzate

### Gestione dello stato
- **TanStack Query** per lo stato server: fetching, caching, invalidazione, sincronizzazione con il backend. In un gestionale la maggior parte dello stato è "dati dal server", quindi questa libreria copre la maggioranza dei casi ed è oggi lo standard di fatto in ambito React.
- **Zustand** per lo stato client puro (es. sidebar aperta/chiusa, tema, filtri temporanei di UI). Alternativa più strutturata: **Redux Toolkit**, utile solo se il progetto cresce molto in complessità e serve un flusso dati più rigido/tracciabile.

### UI Kit / Componenti
Due strade principali:
1. **Tailwind CSS + shadcn/ui** — componenti copiati direttamente nel progetto (non una dipendenza "scatola nera"), quindi facilmente personalizzabili al brand/settore del cliente. È oggi la combinazione più diffusa per nuovi progetti React.
2. **MUI (Material UI)** — set di componenti completo "out of the box", utile se serve velocità di sviluppo e coerenza visiva enterprise senza troppa personalizzazione grafica.

(**Ant Design** resta una terza opzione solida, molto orientata a pannelli di amministrazione "densi" di dati.)

### Form
- **React Hook Form** + **Zod** per validazione schema-based e type-safe. Zod permette di condividere gli schemi di validazione anche lato backend, se scritto in TypeScript, evitando di duplicare le regole di validazione.

### Tabelle dati
- **TanStack Table** — headless, per tabelle con sorting, filtri, paginazione: quasi ogni sezione di un gestionale (elenchi clienti, ordini, pratiche...) ne avrà bisogno.

### Grafici / Dashboard
- **Recharts** (più semplice da configurare) o **Chart.js** (più configurabile) per KPI e riepiloghi nella dashboard.

### Internazionalizzazione
- **react-i18next** — utile se il gestionale deve supportare più lingue/mercati.

### Date e orari
- **date-fns** o **Day.js** — manipolazione date leggera.

### Icone
- **lucide-react**

## PWA lato frontend

- **vite-plugin-pwa** genera automaticamente il manifest e il service worker basato su **Workbox**, con configurazione dichiarativa in `vite.config.ts` (nessuna configurazione manuale del service worker necessaria per i casi standard).
- Dettagli tecnici PWA completi (manifest, strategie di caching, offline, installabilità, push) nel file `04-pwa-checklist.md`.

## Struttura cartelle proposta (feature-based)

```
src/
├── app/                  # configurazione app, router, provider globali
├── assets/
├── components/
│   ├── ui/               # componenti UI generici riutilizzabili (bottoni, input, modali)
│   └── layout/           # shell, sidebar, header
├── features/
│   ├── auth/
│   ├── dashboard/
│   ├── anagrafiche/      # modulo CRUD generico, da rinominare/duplicare per settore
│   ├── notifiche/
│   └── impostazioni/
├── hooks/                # custom hook condivisi
├── lib/                  # client API, utility, configurazione
├── stores/               # store Zustand
├── types/
└── main.tsx
```

Ogni cartella dentro `features/` è autonoma: componenti, hook, chiamate API e tipi relativi a quella funzionalità, per mantenere il codice modulare e facilmente estendibile quando si aggiunge un nuovo modulo di settore.

## Testing
- **Vitest** + **React Testing Library** per test unitari e di componente
- **Playwright** per test end-to-end (utile anche per validare i flussi PWA offline/installazione)

## Qualità del codice
- **ESLint** + **Prettier**
- **TypeScript** consigliato in tutto il progetto, per coerenza dei tipi tra frontend e backend (specialmente se anche il backend è in TypeScript)

## Performance e accessibilità
- Code splitting per rotta (`React.lazy` + `Suspense`)
- Memoizzazione mirata (`useMemo`, `useCallback`) solo dove il profiling mostra un reale beneficio, non come abitudine sistematica
- Attenzione a contrasto colori, focus visibile, navigazione da tastiera: importante anche per compliance in alcuni settori (es. pubblica amministrazione, sanità)
