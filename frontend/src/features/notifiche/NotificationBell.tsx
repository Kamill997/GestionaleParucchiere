import { Bell } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

import { useNonLetteCount, useNotifiche, useSegnaLetta, useSegnaTutteLette } from './hooks'
import { PushPrompt } from './PushPrompt'
import type { Notifica } from './types'

function formattaRelativo(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime()
  const minuti = Math.floor(diffMs / 60000)
  if (minuti < 1) return 'adesso'
  if (minuti < 60) return `${minuti} min fa`
  const ore = Math.floor(minuti / 60)
  if (ore < 24) return `${ore} h fa`
  return new Date(iso).toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })
}

/**
 * docs/03-componenti-e-workflow.md, "Notifiche": "In-app, email, push".
 * Dropdown custom leggero (nessuna nuova dipendenza: il progetto non ha
 * ancora un primitivo Popover, solo Dialog che e' pensato per overlay
 * modali, non per un menu ancorato come questo).
 */
export function NotificationBell() {
  const [aperto, setAperto] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  const { data: nonLette } = useNonLetteCount()
  const { data: notifiche, isLoading } = useNotifiche(aperto)
  const segnaLettaMutation = useSegnaLetta()
  const segnaTutteLetteMutation = useSegnaTutteLette()

  useEffect(() => {
    if (!aperto) return
    const handleClick = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setAperto(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [aperto])

  const apriNotifica = (notifica: Notifica) => {
    if (!notifica.letta) segnaLettaMutation.mutate(notifica.id)
    setAperto(false)
    if (notifica.link) navigate(notifica.link)
  }

  return (
    <div ref={containerRef} className="relative">
      <Button
        variant="ghost"
        size="icon"
        aria-label="Notifiche"
        onClick={() => setAperto((v) => !v)}
      >
        <span className="relative inline-flex">
          <Bell className="h-4 w-4" />
          {!!nonLette && nonLette > 0 && (
            <span className="absolute -right-1.5 -top-1.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-danger px-0.5 text-[9px] font-semibold leading-none text-white">
              {nonLette > 9 ? '9+' : nonLette}
            </span>
          )}
        </span>
      </Button>

      {aperto && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-lg border border-border bg-surface shadow-lg">
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <p className="text-sm font-semibold text-ink">Notifiche</p>
            {!!notifiche?.results.length && (
              <button
                onClick={() => segnaTutteLetteMutation.mutate()}
                className="text-xs text-primary hover:underline"
              >
                Segna tutte lette
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-auto">
            {isLoading ? (
              <p className="px-4 py-6 text-center text-sm text-ink-muted">Caricamento…</p>
            ) : !notifiche?.results.length ? (
              <p className="px-4 py-6 text-center text-sm text-ink-muted">Nessuna notifica.</p>
            ) : (
              notifiche.results.map((notifica) => (
                <button
                  key={notifica.id}
                  onClick={() => apriNotifica(notifica)}
                  className={cn(
                    'flex w-full flex-col gap-0.5 border-b border-border px-4 py-3 text-left last:border-b-0 hover:bg-surface-alt',
                    !notifica.letta && 'bg-primary-soft/40',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-ink">{notifica.titolo}</p>
                    {!notifica.letta && <Badge variant="primary">nuova</Badge>}
                  </div>
                  <p className="line-clamp-2 text-xs text-ink-muted">{notifica.messaggio}</p>
                  <p className="text-[11px] text-ink-faint">
                    {formattaRelativo(notifica.creato_il)}
                  </p>
                </button>
              ))
            )}
          </div>
          <PushPrompt />
        </div>
      )}
    </div>
  )
}
