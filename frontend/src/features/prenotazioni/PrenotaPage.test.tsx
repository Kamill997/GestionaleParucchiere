import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

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

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function mockFetchFlussoPrenotazione() {
  let prenotazioneCreata = false

  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()

      if (url.includes('/auth/csrf/')) return jsonResponse({ detail: 'ok' })
      if (url.includes('/auth/me/')) return jsonResponse(UTENTE_MOCK)

      if (url.includes('/servizi/')) {
        return jsonResponse({
          count: 1,
          next: null,
          previous: null,
          results: [
            {
              id: 'serv1',
              nome: 'Taglio',
              descrizione: '',
              categoria: 'Taglio',
              durata_minuti: 30,
              prezzo: '20.00',
              foto: null,
              attivo: true,
            },
          ],
        })
      }
      if (url.includes('/operatori/')) {
        return jsonResponse({
          count: 1,
          next: null,
          previous: null,
          results: [
            {
              id: 'op1',
              email: 'op@example.com',
              nome: 'Giulia',
              specializzazioni: '',
              foto: null,
              attivo: true,
            },
          ],
        })
      }
      if (url.includes('/slot-disponibili/')) {
        return jsonResponse([
          { inizio: '2026-08-03T09:00:00+02:00', fine: '2026-08-03T09:30:00+02:00' },
          { inizio: '2026-08-03T09:15:00+02:00', fine: '2026-08-03T09:45:00+02:00' },
        ])
      }
      if (url.includes('/prenotazioni/') && init?.method === 'POST') {
        prenotazioneCreata = true
        return jsonResponse(
          {
            id: 'pren1',
            cliente: 'cli1',
            operatore: 'op1',
            servizio: 'serv1',
            inizio: '2026-08-03T09:00:00+02:00',
            fine: '2026-08-03T09:30:00+02:00',
            stato: 'confermata',
            note: '',
            creato_il: '2026-01-01T00:00:00Z',
          },
          201,
        )
      }

      return jsonResponse(
        { detail: prenotazioneCreata ? 'ok' : 'not found' },
        prenotazioneCreata ? 200 : 404,
      )
    }),
  )
}

describe('Flusso di prenotazione', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/prenota')
    mockFetchFlussoPrenotazione()
  })

  it('seleziona servizio, operatore, data, slot e conferma', async () => {
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText(/prenota un appuntamento/i)

    await user.selectOptions(await screen.findByLabelText(/servizio/i), 'serv1')
    await user.selectOptions(screen.getByLabelText(/operatore/i), 'op1')
    fireEvent.change(screen.getByLabelText(/giorno/i), { target: { value: '2026-08-03' } })

    const slotButton = await screen.findByRole('button', { name: '09:00' })
    await user.click(slotButton)

    await user.click(screen.getByRole('button', { name: /conferma prenotazione/i }))

    await waitFor(() => {
      expect(screen.getByText(/prenotazione confermata/i)).toBeInTheDocument()
    })
  })
})
