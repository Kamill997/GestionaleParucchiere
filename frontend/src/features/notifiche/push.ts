/**
 * Gestione lato client delle notifiche push Web (docs/04-pwa-checklist.md,
 * "Notifiche push": "Push API + Notification API lato client, chiavi VAPID
 * lato backend"). Chiamato da usePushNotifications sotto.
 *
 * Flusso:
 *  1. Chiedi al backend la chiave pubblica VAPID (GET /notifiche/vapid-public-key/)
 *  2. Chiedi il permesso all'utente (Notification.requestPermission())
 *  3. Crea la PushSubscription tramite il service worker registrato da vite-plugin-pwa
 *  4. Invia la subscription al backend (POST /notifiche/push-subscribe/)
 */

import { apiFetch } from '@/lib/api'

function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  const outputArray = new Uint8Array(rawData.length) as Uint8Array<ArrayBuffer>
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

async function ottieniVapidPublicKey(): Promise<string | null> {
  try {
    const dati = await apiFetch<{ public_key: string }>('/notifiche/vapid-public-key/')
    return dati.public_key
  } catch {
    return null
  }
}

async function ottieniServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) return null
  try {
    return await navigator.serviceWorker.ready
  } catch {
    return null
  }
}

export type StatoPush = 'non_supportato' | 'non_configurato' | 'negato' | 'attivo' | 'inattivo'

/**
 * Attiva le notifiche push per l'utente corrente.
 * Restituisce 'attivo' se tutto è andato a buon fine, altrimenti un
 * codice che descrive il motivo del fallimento.
 */
export async function attivaPushNotifications(): Promise<StatoPush> {
  if (!('Notification' in window) || !('PushManager' in window)) {
    return 'non_supportato'
  }

  const publicKey = await ottieniVapidPublicKey()
  if (!publicKey) {
    // Il backend non ha VAPID configurato
    return 'non_configurato'
  }

  const permesso = await Notification.requestPermission()
  if (permesso !== 'granted') {
    return 'negato'
  }

  const sw = await ottieniServiceWorker()
  if (!sw) return 'non_supportato'

  try {
    const subscription = await sw.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey),
    })

    await apiFetch('/notifiche/push-subscribe/', {
      method: 'POST',
      body: JSON.stringify({ subscription: subscription.toJSON() }),
    })
    return 'attivo'
  } catch {
    return 'inattivo'
  }
}

/** Controlla lo stato corrente del permesso senza chiedere nulla all'utente. */
export function statoPermessoPush(): StatoPush {
  if (!('Notification' in window) || !('PushManager' in window)) return 'non_supportato'
  if (Notification.permission === 'denied') return 'negato'
  if (Notification.permission === 'granted') return 'attivo'
  return 'inattivo'
}
