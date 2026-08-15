# PWA — Requisiti Tecnici e Checklist

## Perché una PWA per un gestionale

- Installabile su desktop e mobile senza passare da store
- Funzionamento (almeno parziale) offline, utile per operatori sul campo con connettività instabile
- Notifiche push native
- Aggiornamenti automatici senza intervento manuale dell'utente

## Web App Manifest

File `manifest.webmanifest`, generato automaticamente da `vite-plugin-pwa` ma utile conoscerne i campi essenziali:

```json
{
  "name": "Nome Completo Gestionale",
  "short_name": "Gestionale",
  "description": "Descrizione breve dell'app",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0f172a",
  "orientation": "any",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

Esempio di configurazione minima in `vite.config.ts` con `vite-plugin-pwa`:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: { /* vedi manifest sopra */ },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.tuodominio\.it\/.*/i,
            handler: 'NetworkFirst',
          },
        ],
      },
    }),
  ],
})
```

## Service Worker e strategie di caching

Tramite **Workbox** (integrato in `vite-plugin-pwa`):

| Tipo di risorsa | Strategia consigliata | Motivo |
|---|---|---|
| Asset statici (JS/CSS/font) | Cache First | Cambiano solo ad ogni deploy, versionati dal build |
| Chiamate API GET (dati poco volatili) | Stale-While-Revalidate | Risposta immediata da cache + aggiornamento in background |
| Chiamate API GET (dati critici/real-time) | Network First | Priorità al dato fresco, fallback su cache solo se offline |
| Chiamate API POST/PUT/DELETE | Nessun caching diretto — gestire in coda offline (vedi sotto) | Le mutazioni non vanno servite dalla cache |

- Gestire l'aggiornamento del service worker con una notifica non invasiva ("Nuova versione disponibile, ricarica per aggiornare") invece di forzare l'aggiornamento silenzioso, per non interrompere un utente a metà di un'operazione.

## Supporto offline

- **IndexedDB** (tramite **Dexie.js** o **idb**) per persistere dati e azioni compiute offline.
- **Background Sync API** per sincronizzare le azioni in coda (es. una modifica salvata offline) non appena torna la connessione.
- Feedback UI chiaro: banner "Sei offline" + indicatore di elementi "in attesa di sincronizzazione".

## Installabilità

Requisiti tecnici richiesti dai browser (Chrome/Edge) per proporre l'installazione:
- Sito servito in **HTTPS**
- Manifest valido collegato via `<link rel="manifest">`
- Service worker registrato con almeno un handler `fetch`
- Icone di dimensioni adeguate (minimo 192×192 e 512×512, più una versione "maskable")

- Gestire l'evento `beforeinstallprompt` per mostrare un pulsante "Installa app" personalizzato invece di affidarsi solo al prompt automatico del browser.
- Su iOS/Safari il supporto PWA è più limitato (nessun prompt automatico, alcune API assenti): va verificato separatamente se il pubblico target usa molto iPhone/iPad.

## Notifiche push

- **Push API** + **Notification API** lato client
- Richiede un backend che generi e invii notifiche via **Web Push protocol** con chiavi **VAPID**
- Libreria backend consigliata: **pywebpush** (Python)
- Da usare con moderazione: chiedere il permesso solo dopo un'azione contestuale dell'utente, non al primo accesso

## Performance e audit

- **Lighthouse** (integrato in Chrome DevTools) per l'audit PWA completo: installabilità, performance, best practice, accessibilità
- Monitorare i **Core Web Vitals** (LCP, INP, CLS)

## Checklist rapida pre-rilascio

- [ ] Manifest completo con tutte le icone richieste
- [ ] Service worker registrato correttamente in produzione (verificare anche in incognito)
- [ ] App installabile su Android, iOS (supporto parziale/diverso su Safari) e desktop
- [ ] Comportamento offline testato (cosa succede se cade la connessione a metà di un'operazione?)
- [ ] Notifiche push testate su almeno due browser diversi
- [ ] Audit Lighthouse con punteggio PWA verde
- [ ] HTTPS attivo su tutti gli ambienti, incluso staging
