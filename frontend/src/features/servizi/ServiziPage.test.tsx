import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from '@/app/App'

const SERVIZIO_MOCK = {
  id: 's1',
  nome: 'Taglio uomo',
  descrizione: '',
  categoria: 'Taglio',
  durata_minuti: 30,
  prezzo: '20.00',
  foto: null,
  attivo: true,
}

function mockFetchPer(ruoli: string[]) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()

      if (url.includes('/auth/csrf/')) {
        return new Response(JSON.stringify({ detail: 'ok' }), { status: 200 })
      }
      if (url.includes('/auth/login/') && init?.method === 'POST') {
        return new Response(
          JSON.stringify({
            id: 'u1',
            email: 'test@example.com',
            nome: 'Test',
            cognome: '',
            stato: 'attivo',
            ruoli,
            is_staff: false,
            date_joined: '2026-01-01T00:00:00Z',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        )
      }
      if (url.includes('/auth/me/')) {
        return new Response(
          JSON.stringify({
            id: 'u1',
            email: 'test@example.com',
            nome: 'Test',
            cognome: '',
            stato: 'attivo',
            ruoli,
            is_staff: false,
            date_joined: '2026-01-01T00:00:00Z',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        )
      }
      if (url.includes('/servizi/')) {
        return new Response(
          JSON.stringify({ count: 1, next: null, previous: null, results: [SERVIZIO_MOCK] }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        )
      }
      return new Response(JSON.stringify({ detail: 'not found' }), { status: 404 })
    }),
  )
}

describe('ServiziPage', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/servizi')
  })

  it('un Cliente vede il catalogo ma non le azioni di gestione', async () => {
    mockFetchPer(['Cliente'])
    render(<App />)

    expect(await screen.findByText('Taglio uomo')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /nuovo servizio/i })).not.toBeInTheDocument()
  })

  it('un Amministratore vede anche le azioni di gestione', async () => {
    mockFetchPer(['Amministratore'])
    render(<App />)

    expect(await screen.findByText('Taglio uomo')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /nuovo servizio/i })).toBeInTheDocument()
    })
  })
})
