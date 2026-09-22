import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { NotFoundPage } from './NotFoundPage'
import { PrivacyPage } from './PrivacyPage'
import { TerminiPage } from './TerminiPage'

describe('Pagine informative e di errore', () => {
  it('NotFoundPage mostra codice 404 e pulsante di ritorno', () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>,
    )

    expect(screen.getByText('404')).toBeInTheDocument()
    expect(screen.getByText('Pagina non trovata')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /torna alla dashboard/i })).toBeInTheDocument()
  })

  it('PrivacyPage mostra informativa GDPR', () => {
    render(
      <MemoryRouter>
        <PrivacyPage />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: /informativa sulla privacy/i })).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: /1\. titolare del trattamento/i }),
    ).toBeInTheDocument()
    expect(screen.getAllByText(/GDPR/i).length).toBeGreaterThanOrEqual(1)
  })

  it('TerminiPage mostra politica di cancellazione e no-show', () => {
    render(
      <MemoryRouter>
        <TerminiPage />
      </MemoryRouter>,
    )

    expect(
      screen.getByRole('heading', { name: /termini e condizioni di servizio/i }),
    ).toBeInTheDocument()
    expect(screen.getByText(/politica di cancellazione/i)).toBeInTheDocument()
    expect(screen.getByText(/politica no-show/i)).toBeInTheDocument()
  })
})
