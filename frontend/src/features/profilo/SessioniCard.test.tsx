import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { ToastProvider } from '@/components/ui/toast'
import * as authApi from '@/features/auth/api'
import type { UserSession } from '@/features/auth/types'
import { SessioniCard } from './SessioniCard'

vi.mock('@/features/auth/api', async (importOriginal) => {
  const actual = await importOriginal<typeof authApi>()
  return {
    ...actual,
    fetchSessioni: vi.fn(),
    revocaSessione: vi.fn(),
    revocaAltreSessioni: vi.fn(),
    revocaTutteSessioni: vi.fn(),
  }
})

describe('SessioniCard', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
  })

  const mockSessions: UserSession[] = [
    {
      id: 'session-1',
      dispositivo: 'Chrome su Windows',
      ip_address: '127.0.0.1',
      creato_il: '2026-09-19T10:00:00Z',
      ultimo_accesso: '2026-09-19T12:00:00Z',
      revocata: false,
      e_corrente: true,
    },
    {
      id: 'session-2',
      dispositivo: 'Safari su iPhone',
      ip_address: '192.168.1.50',
      creato_il: '2026-09-18T08:00:00Z',
      ultimo_accesso: '2026-09-18T18:00:00Z',
      revocata: false,
      e_corrente: false,
    },
  ]

  it('mostra i dispositivi attivi distinguendo quello corrente', async () => {
    vi.mocked(authApi.fetchSessioni).mockResolvedValue(mockSessions)

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ToastProvider>
            <SessioniCard />
          </ToastProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Chrome su Windows')).toBeInTheDocument()
    })
    expect(screen.getByText('Safari su iPhone')).toBeInTheDocument()
    expect(screen.getByText('Dispositivo attuale')).toBeInTheDocument()
    expect(screen.getByText(/127\.0\.0\.1/)).toBeInTheDocument()
    expect(screen.getByText(/192\.168\.1\.50/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /disconnetti altri dispositivi/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /disconnetti ovunque/i })).toBeInTheDocument()
  })

  it('apre la modale di conferma quando si clicca su Disconnetti per una sessione remota', async () => {
    const user = userEvent.setup()
    vi.mocked(authApi.fetchSessioni).mockResolvedValue(mockSessions)

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ToastProvider>
            <SessioniCard />
          </ToastProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Safari su iPhone')).toBeInTheDocument()
    })

    const disconnettiBtn = screen.getByRole('button', { name: /^disconnetti$/i })
    await user.click(disconnettiBtn)

    expect(screen.getByRole('heading', { name: /disconnetti dispositivo/i })).toBeInTheDocument()
    expect(
      screen.getByText(/sei sicuro di voler terminare questa sessione/i),
    ).toBeInTheDocument()
  })
})
