export function KpiCard({
  etichetta,
  valore,
  dettaglio,
}: {
  etichetta: string
  valore: string
  dettaglio?: string
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">{etichetta}</p>
      <p className="mt-1 font-display text-2xl font-semibold text-ink">{valore}</p>
      {dettaglio && <p className="mt-1 text-xs text-ink-muted">{dettaglio}</p>}
    </div>
  )
}
