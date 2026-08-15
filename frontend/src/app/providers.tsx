import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import { ToastProvider } from '@/components/ui/toast'

import { ErrorBoundary } from './ErrorBoundary'

// Istanza singola di QueryClient per l'intera app (esportata: i test la
// azzerano tra un caso e l'altro con queryClient.clear(), altrimenti dati
// come l'utente corrente resterebbero in cache da un test al successivo).
export const queryClient = new QueryClient()

/**
 * Raccoglie tutti i provider globali dell'applicazione in un unico punto,
 * cosi' main.tsx resta minimale e i test possono avvolgere i componenti
 * con lo stesso set di provider usato in produzione.
 */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ToastProvider>{children}</ToastProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
