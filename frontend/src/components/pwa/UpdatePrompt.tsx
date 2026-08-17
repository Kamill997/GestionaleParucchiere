import { RefreshCw } from 'lucide-react'
import { useRegisterSW } from 'virtual:pwa-register/react'

import { Button } from '@/components/ui/button'

/**
 * docs/04-pwa-checklist.md, "Service Worker e strategie di caching":
 * "Gestire l'aggiornamento del service worker con una notifica non invasiva
 * ... invece di forzare l'aggiornamento silenzioso, per non interrompere un
 * utente a metà di un'operazione." Per questo `registerType: 'prompt'` in
 * vite.config.ts invece di 'autoUpdate': il reload avviene solo su
 * conferma esplicita qui sotto, mai da solo.
 *
 * `offlineReady` copre invece il primo avvio (SW installato, app pronta
 * per funzionare offline): banner informativo, si chiude da solo.
 */
export function UpdatePrompt() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    offlineReady: [offlineReady, setOfflineReady],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW(_url, registration) {
      // Controlla se c'e' una nuova versione ogni ora: utile per un'app
      // aperta a lungo in un salone durante il giorno lavorativo, senza
      // affidarsi solo al refresh di pagina per scoprire aggiornamenti.
      if (!registration) return
      setInterval(() => registration.update(), 60 * 60 * 1000)
    },
  })

  if (!needRefresh && !offlineReady) return null

  const chiudi = () => {
    setNeedRefresh(false)
    setOfflineReady(false)
  }

  return (
    <div className="fixed inset-x-4 bottom-4 z-50 mx-auto flex max-w-md items-center justify-between gap-3 rounded-lg border border-border bg-surface p-4 shadow-lg sm:inset-x-auto sm:right-4">
      {needRefresh ? (
        <>
          <div className="flex items-center gap-2 text-sm text-ink">
            <RefreshCw className="h-4 w-4 shrink-0 text-primary" />
            Nuova versione disponibile.
          </div>
          <div className="flex shrink-0 gap-2">
            <Button variant="ghost" size="sm" onClick={chiudi}>
              Dopo
            </Button>
            <Button size="sm" onClick={() => updateServiceWorker(true)}>
              Ricarica
            </Button>
          </div>
        </>
      ) : (
        <>
          <p className="text-sm text-ink-muted">App pronta per funzionare offline.</p>
          <Button variant="ghost" size="sm" onClick={chiudi}>
            Ok
          </Button>
        </>
      )}
    </div>
  )
}
