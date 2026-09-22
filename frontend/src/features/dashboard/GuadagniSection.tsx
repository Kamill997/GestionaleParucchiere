import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'

import { Badge } from '@/components/ui/badge'

import { AndamentoProfittiChart } from './AndamentoProfittiChart'
import { RipartizioneCategoriaChart } from './RipartizioneCategoriaChart'
import { useAndamentoProfitti, useReportGuadagni, type GuadagnoRiga } from './hooks'

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
 * docs/08-pagamenti.md, "Dashboard guadagni (lato Amministratore)":
 * Grafici di andamento temporale del profitto (Line Chart), ripartizione per categoria
 * di servizio (Donut Chart) e riepilogo dettagliato delle performance.
 */
export function GuadagniSection() {
  const [giorni, setGiorni] = useState(30)
  const { data: report, isLoading: isLoadingReport } = useReportGuadagni()
  const { data: andamento, isLoading: isLoadingAndamento } = useAndamentoProfitti(giorni)

  if (isLoadingReport && isLoadingAndamento) {
    return <p className="text-sm text-ink-muted">Caricamento analitiche e guadagni…</p>
  }

  return (
    <div className="mt-8 space-y-6">
      <div>
        <h2 className="font-display text-lg font-semibold text-ink">Analitiche & Guadagni</h2>
        <p className="text-sm text-ink-muted">
          Panoramica economica e andamento delle vendite riservata alla direzione del salone.
        </p>
      </div>

      {andamento && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <AndamentoProfittiChart
              giorni={andamento.giorni}
              totalePeriodo={andamento.totale_periodo}
              mediaGiornaliera={andamento.media_giornaliera}
              giorniSelezionati={giorni}
              onCambiaGiorni={setGiorni}
            />
          </div>
          <div>
            <RipartizioneCategoriaChart
              categorie={andamento.categorie}
              totalePeriodo={andamento.totale_periodo}
            />
          </div>
        </div>
      )}

      {report && (
        <div>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-muted">
            Riepilogo Dettagliato
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
    )}
  </div>
  )
}
