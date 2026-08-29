/**
 * Service worker custom per le notifiche push (docs/04-pwa-checklist.md,
 * "Notifiche push": "handler 'push' nel service worker").
 *
 * vite-plugin-pwa supporta un service worker personalizzato tramite
 * strategies: 'injectManifest' in vite.config.ts: il build tool inietta
 * il precache Workbox in questo file invece di generarne uno da zero.
 * Poi registra qui l'handler per l'evento 'push' che Workbox non copre.
 *
 * NOTA: questo file è referenziato da vite.config.ts (non ancora - vedi
 * commento inline), che attualmente usa strategies: 'generateSW' (default).
 * Per attivare il service worker custom:
 *   1. Spostare questo file in frontend/src/sw.ts
 *   2. In vite.config.ts cambiare VitePWA({ strategies: 'injectManifest',
 *      srcDir: 'src', filename: 'sw.ts', ... })
 *
 * Con 'generateSW' (configurazione attuale) le notifiche push arrivano al
 * backend e vengono inviate al browser, ma il browser non mostra ancora
 * la notifica nativa perché manca questo handler. Il cambio di strategia
 * è il passo finale che completa il flusso push end-to-end.
 */

/// <reference lib="webworker" />
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { NetworkFirst, StaleWhileRevalidate } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'

declare const self: ServiceWorkerGlobalScope

// Workbox inietterà qui il precache manifest a build time
precacheAndRoute(self.__WB_MANIFEST)
cleanupOutdatedCaches()

// --- Strategie di caching runtime (docs/04-pwa-checklist.md) ---

// Catalogo (poco volatile): risposta immediata da cache + aggiornamento in background
registerRoute(
  ({ url }) => /\/api\/v1\/(servizi|operatori|disponibilita)\//.test(url.pathname),
  new StaleWhileRevalidate({
    cacheName: 'catalogo-api-cache',
    plugins: [new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 86400 })],
  }),
)

// Dati critici/real-time: priorità al dato fresco, cache solo come fallback offline
registerRoute(
  ({ url }) =>
    /\/api\/v1\/(prenotazioni|clienti|admin|dashboard|slot-disponibili)\//.test(url.pathname),
  new NetworkFirst({
    cacheName: 'dati-critici-api-cache',
    networkTimeoutSeconds: 5,
    plugins: [new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 300 })],
  }),
)
// Mutazioni (POST/PUT/DELETE): MAI in cache — Workbox registra solo GET di default
// con registerRoute, quindi le mutazioni non vengono intercettate.

/**
 * Evento push: arriva dal backend quando pywebpush invia una notifica
 * (vedi backend/apps/notifiche/push_services.py). Il payload è il JSON
 * con {title, body, url} serializzato in push_services.py.
 */
self.addEventListener('push', (event) => {
  if (!event.data) return

  let payload: { title?: string; body?: string; url?: string } = {}
  try {
    payload = event.data.json()
  } catch {
    payload = { title: 'Notifica', body: event.data.text() }
  }

  const title = payload.title ?? 'Gestionale Salone'
  const options: NotificationOptions = {
    body: payload.body ?? '',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    data: { url: payload.url ?? '/' },
    // vibrate non è in tutti i browser ma viene ignorato dove non supportato
    // @ts-ignore
    vibrate: [100, 50, 100],
  }

  event.waitUntil(self.registration.showNotification(title, options))
})

/**
 * Click sulla notifica nativa: apre (o porta in primo piano) la finestra
 * del browser sul percorso indicato da data.url.
 */
self.addEventListener('notificationclick', (event) => {
  event.notification.close()

  const targetUrl = (event.notification.data?.url as string) ?? '/'

  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Se c'è già una finestra aperta su questo dominio, la porta in
        // primo piano e naviga all'URL invece di aprirne un'altra.
        for (const client of clientList) {
          if ('focus' in client) {
            client.focus()
            // postMessage usato perché client.navigate() è disponibile solo
            // per i client controllati (non sempre il caso).
            client.postMessage({ type: 'NAVIGATE', url: targetUrl })
            return
          }
        }
        // Nessuna finestra aperta: aprine una.
        return self.clients.openWindow(targetUrl)
      }),
  )
})
