import { BellRing } from 'lucide-react'

import { Button } from '@/components/ui/button'

import { usePushNotifications } from './usePushNotifications'

/**
 * Banner discreto, mostrato in fondo al dropdown NotificationBell quando le
 * notifiche push non sono ancora attive (stato 'inattivo'). Non viene mai
 * mostrato se il browser non le supporta o se l'utente le ha già negate
 * (non ha senso chiedere di nuovo, e il browser ignorerebbe la seconda
 * richiesta).
 *
 * docs/04-pwa-checklist.md: "usare con moderazione: chiedere il permesso
 * solo dopo un'azione contestuale dell'utente, non al primo accesso" -
 * qui il contesto è l'apertura del pannello notifiche, che è già un segnale
 * di interesse alle notifiche.
 */
export function PushPrompt() {
  const { stato, loading, attiva } = usePushNotifications()

  // Mostra solo se il permesso non è ancora stato dato (e non è negato/non supportato)
  if (stato !== 'inattivo') return null

  return (
    <div className="border-t border-border bg-surface-alt/60 px-4 py-3">
      <div className="flex items-center gap-2">
        <BellRing className="h-4 w-4 shrink-0 text-primary" />
        <div className="flex-1">
          <p className="text-xs font-medium text-ink">Attiva le notifiche push</p>
          <p className="text-xs text-ink-muted">
            Ricevi avvisi anche quando non hai l'app aperta.
          </p>
        </div>
        <Button size="sm" variant="secondary" onClick={attiva} disabled={loading}>
          {loading ? 'Attivazione…' : 'Attiva'}
        </Button>
      </div>
    </div>
  )
}
