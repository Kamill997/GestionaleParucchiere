import { Download } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

/**
 * docs/04-pwa-checklist.md, "Installabilità": "Gestire l'evento
 * beforeinstallprompt per mostrare un pulsante 'Installa app' personalizzato
 * invece di affidarsi solo al prompt automatico del browser."
 *
 * Su iOS/Safari questo evento non esiste (vedi stesso file, "supporto PWA
 * più limitato, nessun prompt automatico"): il componente semplicemente non
 * renderizza nulla li', non c'e' un fallback dedicato per l'aggiunta
 * manuale a schermata Home in questa prima versione.
 */
export function InstallButton() {
  const [installEvent, setInstallEvent] = useState<BeforeInstallPromptEvent | null>(null)

  useEffect(() => {
    const handler = (event: Event) => {
      event.preventDefault()
      setInstallEvent(event as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  if (!installEvent) return null

  const installa = async () => {
    await installEvent.prompt()
    const scelta = await installEvent.userChoice
    if (scelta.outcome === 'accepted') {
      setInstallEvent(null)
    }
  }

  return (
    <Button variant="secondary" size="sm" onClick={installa}>
      <Download className="h-4 w-4" />
      Installa app
    </Button>
  )
}
