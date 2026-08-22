import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import App from '@/app/App'

const UTENTE_MOCK = {
  id: 'u1',
  email: 'cliente@example.com',
  nome: 'Mario',
  cognome: '',
  stato: 'attivo',
  ruoli: ['Cliente'],
  is_staff: false,
  date_joined: '2026-01-01T00:00:00Z',
}

const NOTIFICA_MOCK = {
  id: 'n1',
  tipo: 'conferma_prenotazione',
  titolo: 'Prenotazione confermata',
  messaggio: 'Il tuo appuntamento è confermato.',
  link: '/le-mie-prenotazioni',
  letta: false,
  creato_il: new Date().toISOString(),
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function mockFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()

      if (url.includes('/auth/csrf/')) return jsonResponse({ detail: 'ok' })
      if (url.includes('/auth/me/')) return jsonResponse(UTENTE_MOCK)
      if (url.includes('/notifiche/non-lette-count/')) return jsonResponse({ conteggio: 1 })
      if (url.includes('/notifiche/') && url.includes('segna-letta') && init?.method === 'POST') {
        return jsonResponse({ ...NOTIFICA_MOCK, letta: true })
      }
      if (url.includes('/notifiche/')) {
        return jsonResponse({ count: 1, next: null, previous: null, results: [NOTIFICA_MOCK] })
      }
      return jsonResponse({ detail: 'not found' }, 404)
    }),
  )
}

describe('NotificationBell', () => {
  it('mostra il badge non lette e apre la lista al click', async () => {
    window.history.pushState({}, '', '/')
    mockFetch()
    const user = userEvent.setup()
    render(<App />)

    await screen.findByLabelText(/notifiche/i)
    expect(await screen.findByText('1')).toBeInTheDocument()

    await user.click(screen.getByLabelText(/notifiche/i))

    expect(await screen.findByText('Prenotazione confermata')).toBeInTheDocument()
  })

  it('segna come letta al click sulla notifica', async () => {
    window.history.pushState({}, '', '/')
    mockFetch()
    const user = userEvent.setup()
    render(<App />)

    await user.click(await screen.findByLabelText(/notifiche/i))
    await user.click(await screen.findByText('Prenotazione confermata'))

    await waitFor(() => {
      const chiamate = vi.mocked(fetch).mock.calls.map(([input]) => input.toString())
      expect(chiamate.some((url) => url.includes('/notifiche/n1/segna-letta/'))).toBe(true)
    })
  })
})
