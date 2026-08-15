import { AlertTriangle } from 'lucide-react'

import { Badge } from '@/components/ui/badge'

import { useReportGuadagni, type GuadagnoRiga } from './hooks'

function ListaGuadagni({ righe, vuoto }: { righe: GuadagnoRiga[]; vuoto: string }) {
  if (righe.length === 0) {
    return <p className="text-sm text-ink-muted">{vuoto}</p>
  }
  return (
    <ul className="space-y-1.5">
      {righe.map((riga) => (
        <li key={riga.nome} className="flex items-center justify-between text-sm">
          <span className="text-ink">{riga.nome}</span>
          <span className="font-mono text-ink-muted">€ {riga.totale}</span>
        </li>
      ))}
    </ul>
  )
}

/**
 * docs/08-pagamenti.md, "Dashboard guadagni (lato Amministratore)": ultimo
 * pezzo del checklist del modulo pagamenti (guadagni per cliente/servizio/
 * operatore + elenco clienti vicini alla soglia di blocco). Il totale
 * aggregato (fatturato_settimana) resta nelle KpiCard sopra, invariato:
 * questa e' solo la vista di dettaglio, riservata ad Amministratore.
 */
export function GuadagniSection() {
  const { data: report, isLoading } = useReportGuadagni()

  if (isLoading) return <p className="text-sm text-ink-muted">Caricamento guadagni…</p>
  if (!report) return null

  return (
    <div className="mt-8">
      <h2 className="font-display text-lg font-semibold text-ink">Guadagni</h2>
      <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">
            Per servizio (7 giorni)
          </p>
          <ListaGuadagni
            righe={report.per_servizio}
            vuoto="Nessun incasso negli ultimi 7 giorni."
          />
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">
            Per operatore (7 giorni)
          </p>
          <ListaGuadagni
            righe={report.per_operatore}
            vuoto="Nessun incasso negli ultimi 7 giorni."
          />
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">
            Clienti di maggior valore (storico)
          </p>
          <ListaGuadagni righe={report.top_clienti} vuoto="Nessun incasso registrato ancora." />
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-ink-muted">
            <AlertTriangle className="h-3.5 w-3.5" />
            Vicini al blocco no-show
          </p>
          {report.clienti_vicini_al_blocco.length === 0 ? (
            <p className="text-sm text-ink-muted">Nessun cliente vicino alla soglia.</p>
          ) : (
            <ul className="space-y-1.5">
              {report.clienti_vicini_al_blocco.map((cliente) => (
                <li key={cliente.nome} className="flex items-center justify-between text-sm">
                  <span className="text-ink">{cliente.nome}</span>
                  <Badge variant="warning">
                    {cliente.contatore_no_show}/{cliente.soglia}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
