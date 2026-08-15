import '@testing-library/jest-dom/vitest'
import { afterEach, beforeEach, vi } from 'vitest'

import { queryClient } from '@/app/providers'

// Nessun backend reale in ambiente Vitest: senza un mock, useCurrentUser()
// farebbe un fetch di rete vero (fallirebbe in modo non deterministico).
// Di default si simula un visitatore non autenticato (401 su /auth/me/),
// lo stato piu' comune da cui parte l'app.
beforeEach(() => {
  // Il QueryClient e' un singleton di modulo (necessario in produzione:
  // un'unica sessione browser). Nei test pero' piu' "scenari" girano nello
  // stesso processo: senza azzerarla, la cache di un test (es. utente con
  // ruolo Cliente) contaminerebbe quello successivo (bug reale osservato).
  queryClient.clear()

  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/auth/csrf/')) {
        return new Response(JSON.stringify({ detail: 'Cookie CSRF impostato.' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({ detail: 'Non autenticato.' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      })
    }),
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
})
