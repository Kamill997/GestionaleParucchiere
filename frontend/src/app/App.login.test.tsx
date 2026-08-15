import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'

function mockFetchSequence() {
  let loggedIn = false

  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()

      if (url.includes('/auth/csrf/')) {
        return new Response(JSON.stringify({ detail: 'ok' }), { status: 200 })
      }

      if (url.includes('/auth/login/') && init?.method === 'POST') {
        loggedIn = true
        return new Response(
          JSON.stringify({
            id: 'u1',
            email: 'admin@example.com',
            nome: 'Maria',
            cognome: 'Rossi',
            stato: 'attivo',
            ruoli: ['Amministratore'],
            is_staff: false,
            date_joined: '2026-01-01T00:00:00Z',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        )
      }

      if (url.includes('/auth/me/')) {
        return loggedIn
          ? new Response(
              JSON.stringify({
                id: 'u1',
                email: 'admin@example.com',
                nome: 'Maria',
                cognome: 'Rossi',
                stato: 'attivo',
                ruoli: ['Amministratore'],
                is_staff: false,
                date_joined: '2026-01-01T00:00:00Z',
              }),
              { status: 200, headers: { 'Content-Type': 'application/json' } },
            )
          : new Response(JSON.stringify({ detail: 'Non autenticato.' }), { status: 401 })
      }

      return new Response(JSON.stringify({ detail: 'not found' }), { status: 404 })
    }),
  )
}

describe('Flusso di login', () => {
  beforeEach(() => {
    mockFetchSequence()
  })

  it('login riuscito porta alla dashboard con i dati utente', async () => {
    const user = userEvent.setup()
    render(<App />)

    await screen.findByRole('heading', { name: /gestionale salone/i })

    await user.type(screen.getByLabelText(/email/i), 'admin@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password-corretta')
    await user.click(screen.getByRole('button', { name: /accedi/i }))

    expect(await screen.findByText(/ciao, maria/i)).toBeInTheDocument()
    expect(screen.getByText('Amministratore')).toBeInTheDocument()
  })
})
