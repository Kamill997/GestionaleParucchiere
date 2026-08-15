import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute } from '@/features/auth/ProtectedRoute'

import { AppProviders } from './providers'

// Code splitting per rotta (vedi docs/01-frontend.md, "Performance e
// accessibilità"): ogni pagina diventa un chunk separato invece di gonfiare
// il bundle iniziale.
const LoginPage = lazy(() =>
  import('@/features/auth/LoginPage').then((m) => ({ default: m.LoginPage })),
)
const DashboardPage = lazy(() =>
  import('@/features/dashboard/DashboardPage').then((m) => ({ default: m.DashboardPage })),
)
const ServiziPage = lazy(() =>
  import('@/features/servizi/ServiziPage').then((m) => ({ default: m.ServiziPage })),
)
const PrenotaPage = lazy(() =>
  import('@/features/prenotazioni/PrenotaPage').then((m) => ({ default: m.PrenotaPage })),
)
const LeMiePrenotazioniPage = lazy(() =>
  import('@/features/prenotazioni/LeMiePrenotazioniPage').then((m) => ({
    default: m.LeMiePrenotazioniPage,
  })),
)
const OperatoriPage = lazy(() =>
  import('@/features/operatori/OperatoriPage').then((m) => ({ default: m.OperatoriPage })),
)
const UtentiPage = lazy(() =>
  import('@/features/utenti/UtentiPage').then((m) => ({ default: m.UtentiPage })),
)
const GestionePrenotazioniPage = lazy(() =>
  import('@/features/prenotazioni/GestionePrenotazioniPage').then((m) => ({
    default: m.GestionePrenotazioniPage,
  })),
)
const ClientiPage = lazy(() =>
  import('@/features/clienti/ClientiPage').then((m) => ({ default: m.ClientiPage })),
)

function CaricamentoPagina() {
  return <div className="p-6 text-sm text-ink-muted">Caricamento…</div>
}

export default function App() {
  return (
    <AppProviders>
      <Suspense fallback={<CaricamentoPagina />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/servizi" element={<ServiziPage />} />
              <Route path="/prenota" element={<PrenotaPage />} />
              <Route path="/le-mie-prenotazioni" element={<LeMiePrenotazioniPage />} />
              <Route path="/operatori" element={<OperatoriPage />} />
              <Route path="/clienti" element={<ClientiPage />} />
              <Route path="/utenti" element={<UtentiPage />} />
              <Route path="/gestione-prenotazioni" element={<GestionePrenotazioniPage />} />
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </AppProviders>
  )
}
