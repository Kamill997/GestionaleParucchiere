import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ToastProvider } from '@/components/ui/toast'
import { EccezioniOperatoreDialog } from './EccezioniOperatoreDialog'
import type { Operatore } from './types'

const OPERATORE_MOCK: Operatore = {
  id: 'op-123',
  email: 'chiara@example.com',
  nome: 'Chiara',
  specializzazioni: 'Colore, Piega',
  foto: null,
  attivo: true,
}

function renderConProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>,
  )
}

describe('EccezioniOperatoreDialog', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('mostra le assenze registrate per un operatore e consente di aprire il form', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = typeof input === 'string' ? input : input.toString()
        if (url.includes('/eccezioni-disponibilita/')) {
          return new Response(
            JSON.stringify({
              count: 1,
              next: null,
              previous: null,
              results: [
                {
                  id: 'ecc-1',
                  operatore: 'op-123',
                  operatore_nome: 'Chiara',
                  tipo: 'ferie',
                  data_inizio: '2026-08-10',
                  data_fine: '2026-08-20',
                  ora_inizio: null,
                  ora_fine: null,
                  motivo: 'Vacanze estive',
                  creato_il: '2026-01-01T00:00:00Z',
                },
              ],
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          )
        }
        return new Response(JSON.stringify({}), { status: 200 })
      }),
    )

    renderConProviders(
      <EccezioniOperatoreDialog open={true} onOpenChange={vi.fn()} operatore={OPERATORE_MOCK} />,
    )

    expect(await screen.findByText('Ferie e assenze — Chiara')).toBeInTheDocument()
    expect(await screen.findByText('Vacanze estive')).toBeInTheDocument()

    const btnAggiungi = screen.getByRole('button', { name: /aggiungi assenza/i })
    fireEvent.click(btnAggiungi)

    expect(screen.getByText(/nuovo periodo/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/dal giorno/i)).toBeInTheDocument()
  })

  it('mostra la modalita Chiusure Salone quando operatore e null', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = typeof input === 'string' ? input : input.toString()
        if (url.includes('/eccezioni-disponibilita/')) {
          return new Response(
            JSON.stringify({
              count: 1,
              next: null,
              previous: null,
              results: [
                {
                  id: 'ecc-salone',
                  operatore: null,
                  operatore_nome: null,
                  tipo: 'chiusura',
                  data_inizio: '2026-12-25',
                  data_fine: '2026-12-26',
                  ora_inizio: null,
                  ora_fine: null,
                  motivo: 'Natale e Santo Stefano',
                  creato_il: '2026-01-01T00:00:00Z',
                },
              ],
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          )
        }
        return new Response(JSON.stringify({}), { status: 200 })
      }),
    )

    renderConProviders(
      <EccezioniOperatoreDialog open={true} onOpenChange={vi.fn()} operatore={null} />,
    )

    expect(
      await screen.findByText(/chiusure straordinarie del salone/i),
    ).toBeInTheDocument()
    expect(await screen.findByText('Natale e Santo Stefano')).toBeInTheDocument()
  })
})
