import { WifiOff } from 'lucide-react'
import { useEffect, useState } from 'react'

/**
 * docs/04-pwa-checklist.md, "Supporto offline": "Feedback UI chiaro:
 * banner 'Sei offline'". Copre solo l'indicatore di stato rete: la coda di
 * sincronizzazione per le azioni compiute offline (IndexedDB/Dexie +
 * Background Sync, stesso paragrafo dei docs) resta fuori da questa prima
 * versione - senza quella, un'azione tentata offline fallisce e basta
 * (nessun dato perso in modo silenzioso: apiFetch propaga l'errore di rete
 * come ApiError/errore generico, gia' gestito dai toast esistenti).
 */
export function OfflineBanner() {
  const [online, setOnline] = useState(navigator.onLine)

  useEffect(() => {
    const setOnlineTrue = () => setOnline(true)
    const setOnlineFalse = () => setOnline(false)
    window.addEventListener('online', setOnlineTrue)
    window.addEventListener('offline', setOnlineFalse)
    return () => {
      window.removeEventListener('online', setOnlineTrue)
      window.removeEventListener('offline', setOnlineFalse)
    }
  }, [])

  if (online) return null

  return (
    <div
      role="status"
      className="flex items-center justify-center gap-2 bg-warning-soft px-4 py-2 text-sm font-medium text-warning"
    >
      <WifiOff className="h-4 w-4" />
      Sei offline. Alcune azioni potrebbero non funzionare finché la connessione non torna.
    </div>
  )
}
