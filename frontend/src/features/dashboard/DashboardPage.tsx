import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useCurrentUser } from '@/features/auth/hooks'
import { useProssimoAppuntamento } from '@/features/prenotazioni/hooks'

import { GuadagniSection } from './GuadagniSection'
import { KpiCard } from './KpiCard'
import { useKPIDashboard } from './hooks'

const RUOLI_STAFF = ['Amministratore', 'Operatore']

function formattaData(iso: string) {
  return new Date(iso).toLocaleString('it-IT', { dateStyle: 'full', timeStyle: 'short' })
}

function DashboardStaff() {
  const { data: user } = useCurrentUser()
  const { data: kpi, isLoading } = useKPIDashboard()
  const eAmministratore = !!user && user.ruoli.includes('Amministratore')

  if (isLoading) return <p className="text-sm text-ink-muted">Caricamento…</p>
  if (!kpi) return null

  return (
    <div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard etichetta="Prenotazioni oggi" valore={String(kpi.prenotazioni_oggi)} />
        <KpiCard etichetta="Prenotazioni (7 giorni)" valore={String(kpi.prenotazioni_settimana)} />
        <KpiCard
          etichetta="Servizio più richiesto"
          valore={kpi.servizio_piu_richiesto?.nome ?? '—'}
          dettaglio={
            kpi.servizio_piu_richiesto
              ? `${kpi.servizio_piu_richiesto.conteggio} prenotazioni`
              : undefined
          }
        />
        <KpiCard etichetta="Occupazione oggi" valore={`${kpi.tasso_occupazione_oggi}%`} />
        <KpiCard
          etichetta="Fatturato (7 giorni)"
          valore={`€ ${kpi.fatturato_settimana}`}
          dettaglio="Solo prenotazioni pagate"
        />
        <KpiCard
          etichetta="Tasso no-show"
          valore={`${kpi.tasso_no_show}%`}
          dettaglio="Appuntamenti passati"
        />
      </div>

      {/* docs/08-pagamenti.md: "Dashboard guadagni (lato Amministratore)" -
          esplicitamente riservata ad Amministratore, a differenza della
          griglia KPI sopra che resta staff-wide (Amministratore+Operatore). */}
      {eAmministratore && <GuadagniSection />}
    </div>
  )
}

function DashboardCliente() {
  const { data: prossimo, isLoading } = useProssimoAppuntamento()

  if (isLoading) return <p className="text-sm text-ink-muted">Caricamento…</p>

  if (!prossimo) {
    return (
      <div className="rounded-lg border border-dashed border-border p-6 text-center">
        <p className="text-sm text-ink-muted">Nessun appuntamento in programma.</p>
        <Button asChild className="mt-3">
          <Link to="/prenota">Prenota ora</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
        Prossimo appuntamento
      </p>
      <p className="mt-1 font-display text-xl font-semibold text-ink">
        {formattaData(prossimo.inizio)}
      </p>
    </div>
  )
}

export function DashboardPage() {
  const { data: user } = useCurrentUser()
  const eStaff = !!user && user.ruoli.some((r) => RUOLI_STAFF.includes(r))

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold text-ink">
        Ciao, {user?.nome || user?.email}
      </h1>
      <div className="mt-6">{eStaff ? <DashboardStaff /> : <DashboardCliente />}</div>
    </div>
  )
}
