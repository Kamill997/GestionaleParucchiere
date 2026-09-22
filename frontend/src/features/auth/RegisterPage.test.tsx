import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { RegisterPage } from './RegisterPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

describe('RegisterPage', () => {
  it('mostra tutti i campi del form di registrazione e i link utili', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(screen.getByRole('heading', { name: /crea il tuo account/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/nome \*/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/cognome/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/telefono/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email \*/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password \*/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/conferma password \*/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /registrati/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /accedi/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /termini/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /privacy policy/i })).toBeInTheDocument()
  })
})
