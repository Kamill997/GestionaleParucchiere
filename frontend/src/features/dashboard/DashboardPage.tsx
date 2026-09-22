import { Link } from 'react-router-dom'
import { Download, ExternalLink } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { useCurrentUser } from '@/features/auth/hooks'
import { generaGoogleCalendarUrl, scaricaFileIcs } from '@/features/prenotazioni/calendarUtils'
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
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          etichetta={eAmministratore ? 'Prenotazioni oggi' : 'I miei appuntamenti oggi'}
          valore={String(kpi.prenotazioni_oggi)}
        />
        <KpiCard
          etichetta={eAmministratore ? 'Prenotazioni (7 giorni)' : 'I miei appuntamenti (7 giorni)'}
          valore={String(kpi.prenotazioni_settimana)}
        />
        <KpiCard
          etichetta={eAmministratore ? 'Servizio più richiesto' : 'Il mio servizio più richiesto'}
          valore={kpi.servizio_piu_richiesto?.nome ?? '—'}
          dettaglio={
            kpi.servizio_piu_richiesto
              ? `${kpi.servizio_piu_richiesto.conteggio} appuntamenti`
              : undefined
          }
        />
        <KpiCard
          etichetta={eAmministratore ? 'Occupazione oggi' : 'La mia occupazione oggi'}
          valore={`${kpi.tasso_occupazione_oggi}%`}
        />
        {eAmministratore && kpi.fatturato_settimana && (
          <KpiCard
            etichetta="Fatturato (7 giorni)"
            valore={`€ ${kpi.fatturato_settimana}`}
            dettaglio="Solo prenotazioni pagate"
          />
        )}
        {eAmministratore && (
          <KpiCard
            etichetta="Tasso no-show"
            valore={`${kpi.tasso_no_show}%`}
            dettaglio="Appuntamenti passati"
          />
        )}
      </div>

      {!eAmministratore && (
        <div className="rounded-lg border border-border bg-surface p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="font-display text-base font-semibold text-ink">La tua agenda di lavoro</h2>
            <p className="text-xs text-ink-muted">Visualizza i tuoi appuntamenti dettagliati sul calendario interattivo.</p>
          </div>
          <Button asChild variant="primary">
            <Link to="/gestione-prenotazioni">Apri la mia agenda</Link>
          </Button>
        </div>
      )}

      {/* docs/08-pagamenti.md: "Dashboard guadagni (lato Amministratore)" -
          esplicitamente riservata ad Amministratore, a differenza della
          griglia KPI sopra che resta staff-wide (Amministratore+Operatore). */}
      {eAmministratore && <GuadagniSection />}
    </div>
  )
}

function DashboardCliente() {
  const { data: prossimo, isLoading } = useProssimoAppuntamento()
  const { showToast } = useToast()

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
    <div className="rounded-lg border border-border bg-surface p-4 sm:p-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
            Prossimo appuntamento
          </p>
          <p className="mt-1 font-display text-xl font-semibold text-ink">
            {formattaData(prossimo.inizio)}
          </p>
          <p className="text-sm text-ink-muted mt-0.5">
            {prossimo.servizio_nome} con {prossimo.operatore_nome}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={async () => {
              try {
                await scaricaFileIcs(prossimo.id)
              } catch {
                showToast('Impossibile scaricare il file calendario', 'error')
              }
            }}
            title="Scarica file iCal (.ics)"
            className="flex items-center gap-1.5"
          >
            <Download className="h-3.5 w-3.5" />
            <span>iCal (.ics)</span>
          </Button>
          <Button
            variant="secondary"
            size="sm"
            asChild
            title="Aggiungi a Google Calendar"
            className="flex items-center gap-1.5"
          >
            <a
              href={generaGoogleCalendarUrl(prossimo)}
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink className="h-3.5 w-3.5 text-primary" />
              <span>Google Calendar</span>
            </a>
          </Button>
        </div>
      </div>
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
