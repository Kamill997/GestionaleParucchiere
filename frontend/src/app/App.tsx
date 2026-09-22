import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { OfflineBanner } from '@/components/pwa/OfflineBanner'
import { UpdatePrompt } from '@/components/pwa/UpdatePrompt'
import { ProtectedRoute } from '@/features/auth/ProtectedRoute'

import { AppProviders } from './providers'

// Code splitting per rotta (vedi docs/01-frontend.md, "Performance e
// accessibilità"): ogni pagina diventa un chunk separato invece di gonfiare
// il bundle iniziale.
const LoginPage = lazy(() =>
  import('@/features/auth/LoginPage').then((m) => ({ default: m.LoginPage })),
)
const RegisterPage = lazy(() =>
  import('@/features/auth/RegisterPage').then((m) => ({ default: m.RegisterPage })),
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
const ImpostazioniPage = lazy(() =>
  import('@/features/impostazioni/ImpostazioniPage').then((m) => ({
    default: m.ImpostazioniPage,
  })),
)
const ProfiloPage = lazy(() =>
  import('@/features/profilo/ProfiloPage').then((m) => ({ default: m.ProfiloPage })),
)
const RichiediResetPasswordPage = lazy(() =>
  import('@/features/auth/RichiediResetPasswordPage').then((m) => ({
    default: m.RichiediResetPasswordPage,
  })),
)
const ResetPasswordConfirmPage = lazy(() =>
  import('@/features/auth/ResetPasswordConfirmPage').then((m) => ({
    default: m.ResetPasswordConfirmPage,
  })),
)
const PrivacyPage = lazy(() =>
  import('@/pages/PrivacyPage').then((m) => ({ default: m.PrivacyPage })),
)
const TerminiPage = lazy(() =>
  import('@/pages/TerminiPage').then((m) => ({ default: m.TerminiPage })),
)
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage })),
)


function CaricamentoPagina() {
  return <div className="p-6 text-sm text-ink-muted">Caricamento…</div>
}

export default function App() {
  return (
    <AppProviders>
      <OfflineBanner />
      <Suspense fallback={<CaricamentoPagina />}>
        <Routes>
          {/* Rotte pubbliche non autenticate */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/password-dimenticata" element={<RichiediResetPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordConfirmPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/termini" element={<TerminiPage />} />

          {/* Rotte autenticate: l'AppShell (sidebar + header) è condivisa */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              {/* Accessibili a tutti i ruoli autenticati */}
              <Route path="/" element={<DashboardPage />} />
              <Route path="/servizi" element={<ServiziPage />} />
              <Route path="/profilo" element={<ProfiloPage />} />

              {/* Solo Cliente: prenotazione self-service e storico personale */}
              <Route element={<ProtectedRoute roles={['Cliente']} />}>
                <Route path="/prenota" element={<PrenotaPage />} />
                <Route path="/le-mie-prenotazioni" element={<LeMiePrenotazioniPage />} />
              </Route>

              {/* Solo Staff (Amministratore + Operatore) */}
              <Route element={<ProtectedRoute roles={['Amministratore', 'Operatore']} />}>
                <Route path="/gestione-prenotazioni" element={<GestionePrenotazioniPage />} />
                <Route path="/clienti" element={<ClientiPage />} />
              </Route>

              {/* Solo Amministratore */}
              <Route element={<ProtectedRoute roles={['Amministratore']} />}>
                <Route path="/operatori" element={<OperatoriPage />} />
                <Route path="/utenti" element={<UtentiPage />} />
                <Route path="/impostazioni" element={<ImpostazioniPage />} />
              </Route>
            </Route>
          </Route>

          {/* Rotta 404 catch-all */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
      <UpdatePrompt />
    </AppProviders>
  )
}
