import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import App from '@/app/App'

const CLIENTE_MOCK = {
  id: 'c1',
  user: null,
  nome: 'Mario Rossi',
  email: 'mario@example.com',
  telefono: '333',
  note_preferenze: '',
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function mockFetchPer(ruoli: string[]) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()

      if (url.includes('/auth/csrf/')) return jsonResponse({ detail: 'ok' })
      if (url.includes('/auth/me/')) {
        return jsonResponse({
          id: 'u1',
          email: 'staff@example.com',
          nome: 'Staff',
          cognome: '',
          stato: 'attivo',
          ruoli,
          is_staff: false,
          date_joined: '2026-01-01T00:00:00Z',
        })
      }
      if (url.includes('/clienti/importa/') && init?.method === 'POST') {
        return jsonResponse({ creati: 2, aggiornati: 0, errori: [], duplicati_interni: [] })
      }
      if (url.includes('/clienti/')) {
        return jsonResponse({ count: 1, next: null, previous: null, results: [CLIENTE_MOCK] })
      }
      return jsonResponse({ detail: 'not found' }, 404)
    }),
  )
}

describe('ClientiPage', () => {
  it('un Amministratore vede i pulsanti Importa/Esporta', async () => {
    window.history.pushState({}, '', '/clienti')
    mockFetchPer(['Amministratore'])
    render(<App />)

    expect(await screen.findByText('Mario Rossi')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /importa/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /esporta/i })).toBeInTheDocument()
  })

  it('un Operatore non vede i pulsanti Importa/Esporta (riservati ad Amministratore)', async () => {
    window.history.pushState({}, '', '/clienti')
    mockFetchPer(['Operatore'])
    render(<App />)

    expect(await screen.findByText('Mario Rossi')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /importa/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /esporta/i })).not.toBeInTheDocument()
  })

  it('il flusso di importazione mostra il report al termine', async () => {
    window.history.pushState({}, '', '/clienti')
    mockFetchPer(['Amministratore'])
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('Mario Rossi')
    await user.click(screen.getByRole('button', { name: /importa/i }))

    const dialog = await screen.findByRole('dialog')
    const file = new File(
      ['nome,email,telefono,note_preferenze\nAnna,anna@example.com,123,'],
      'clienti.csv',
      { type: 'text/csv' },
    )
    await user.upload(within(dialog).getByLabelText(/file/i), file)
    await user.click(within(dialog).getByRole('button', { name: /importa/i }))

    await waitFor(() => {
      expect(within(dialog).getByText('Creati')).toBeInTheDocument()
      expect(within(dialog).getByText('2')).toBeInTheDocument()
    })
  })
})
