import { useCallback, useEffect, useState } from 'react'

import { attivaPushNotifications, statoPermessoPush, type StatoPush } from './push'

/**
 * Hook che espone lo stato push corrente e la funzione per attivarlo.
 * Usato da PushPrompt (sotto) e potenzialmente da altre parti dell'UI.
 */
export function usePushNotifications() {
  const [stato, setStato] = useState<StatoPush>(() => statoPermessoPush())
  const [loading, setLoading] = useState(false)

  // Ri-controlla al mount nel caso in cui l'utente abbia cambiato il
  // permesso dal pannello del browser tra una sessione e l'altra.
  useEffect(() => {
    setStato(statoPermessoPush())
  }, [])

  const attiva = useCallback(async () => {
    setLoading(true)
    const nuovoStato = await attivaPushNotifications()
    setStato(nuovoStato)
    setLoading(false)
    return nuovoStato
  }, [])

  return { stato, loading, attiva }
}
