import { useMemo, useState } from 'react'
import { TrendingUp } from 'lucide-react'

import type { AndamentoGiorno } from './hooks'

interface Props {
  giorni: AndamentoGiorno[]
  totalePeriodo: number
  mediaGiornaliera: number
  giorniSelezionati: number
  onCambiaGiorni: (n: number) => void
}

export function AndamentoProfittiChart({
  giorni,
  totalePeriodo,
  mediaGiornaliera,
  giorniSelezionati,
  onCambiaGiorni,
}: Props) {
  const [hoveredPoint, setHoveredPoint] = useState<AndamentoGiorno | null>(null)
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  // Calcoli SVG
  const width = 680
  const height = 240
  const padLeft = 50
  const padRight = 20
  const padTop = 25
  const padBottom = 35

  const plotWidth = width - padLeft - padRight
  const plotHeight = height - padTop - padBottom

  const maxVal = useMemo(() => {
    const m = Math.max(...giorni.map((g) => g.totale), 0)
    return m > 0 ? Math.ceil(m * 1.15) : 100
  }, [giorni])

  const points = useMemo(() => {
    if (giorni.length === 0) return []
    return giorni.map((g, i) => {
      const x = padLeft + (i / Math.max(giorni.length - 1, 1)) * plotWidth
      const y = padTop + plotHeight - (g.totale / maxVal) * plotHeight
      return { x, y, g, i }
    })
  }, [giorni, maxVal, plotWidth, plotHeight])

  const pathD = useMemo(() => {
    if (points.length === 0) return ''
    return points.reduce((acc, p, i) => {
      if (i === 0) return `M ${p.x} ${p.y}`
      // Calcolo curva morbida (Catmull-Rom / Bézier)
      const prev = points[i - 1]
      const cp1x = prev.x + (p.x - prev.x) / 2
      const cp1y = prev.y
      const cp2x = prev.x + (p.x - prev.x) / 2
      const cp2y = p.y
      return `${acc} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p.x} ${p.y}`
    }, '')
  }, [points])

  const areaD = useMemo(() => {
    if (points.length === 0) return ''
    const first = points[0]
    const last = points[points.length - 1]
    const baseline = padTop + plotHeight
    return `${pathD} L ${last.x} ${baseline} L ${first.x} ${baseline} Z`
  }, [pathD, points, padTop, plotHeight])

  const yTicks = [0, Math.round(maxVal * 0.33), Math.round(maxVal * 0.66), maxVal]

  // Selezione etichette X per non sovraffollare (massimo 7 etichette)
  const stepLabel = Math.max(1, Math.floor(giorni.length / 6))

  return (
    <div className="rounded-lg border border-border bg-surface p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <h3 className="font-display text-base font-semibold text-ink">
              Andamento Profitti e Incassi
            </h3>
          </div>
          <p className="text-xs text-ink-muted mt-0.5">
            Evoluzione del fatturato giornaliero da appuntamenti completati e pagati.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-border bg-surface-alt p-0.5 text-xs font-medium">
            {[7, 14, 30].map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => onCambiaGiorni(n)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  giorniSelezionati === n
                    ? 'bg-primary text-white shadow-xs font-semibold'
                    : 'text-ink-muted hover:text-ink'
                }`}
              >
                {n} giorni
              </button>
            ))}
          </div>

          <div className="border-l border-border pl-3 text-right">
            <span className="text-[10px] text-ink-muted uppercase tracking-wider block">Totale</span>
            <span className="font-mono text-sm font-bold text-ink">€ {totalePeriodo.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Grafico SVG Responsivo */}
      <div className="relative mt-4">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible select-none"
        >
          <defs>
            <linearGradient id="profitAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-primary, #6366f1)" stopOpacity="0.3" />
              <stop offset="100%" stopColor="var(--color-primary, #6366f1)" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Griglia orizzontale & Ticks asse Y */}
          {yTicks.map((val) => {
            const y = padTop + plotHeight - (val / maxVal) * plotHeight
            return (
              <g key={val} className="text-ink-muted/40">
                <line
                  x1={padLeft}
                  y1={y}
                  x2={width - padRight}
                  y2={y}
                  stroke="currentColor"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
                <text
                  x={padLeft - 8}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="currentColor"
                  className="font-mono text-ink-muted"
                >
                  €{val}
                </text>
              </g>
            )
          })}

          {/* Asse X - Etichette date */}
          {points.map((p, i) => {
            if (i % stepLabel !== 0 && i !== points.length - 1) return null
            return (
              <text
                key={p.g.data}
                x={p.x}
                y={height - 8}
                textAnchor="middle"
                fontSize="11"
                className="fill-ink-muted font-medium"
              >
                {p.g.etichetta}
              </text>
            )
          })}

          {/* Area sfumata */}
          {areaD && <path d={areaD} fill="url(#profitAreaGrad)" />}

          {/* Linea principale del grafico */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="var(--color-primary, #6366f1)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Linea verticale guida su hover */}
          {hoveredPoint && hoveredIndex !== null && points[hoveredIndex] && (
            <line
              x1={points[hoveredIndex].x}
              y1={padTop}
              x2={points[hoveredIndex].x}
              y2={padTop + plotHeight}
              stroke="var(--color-primary, #6366f1)"
              strokeWidth="1.5"
              strokeDasharray="3 3"
            />
          )}

          {/* Punti interattivi */}
          {points.map((p) => {
            const isHovered = hoveredIndex === p.i
            return (
              <g
                key={p.g.data}
                className="cursor-pointer"
                onMouseEnter={() => {
                  setHoveredPoint(p.g)
                  setHoveredIndex(p.i)
                }}
                onMouseLeave={() => {
                  setHoveredPoint(null)
                  setHoveredIndex(null)
                }}
              >
                {/* Hitbox trasparente più ampia per facilitare il mouseover */}
                <circle cx={p.x} cy={p.y} r="14" fill="transparent" />
                {/* Punto visibile */}
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={isHovered ? 5.5 : 3.5}
                  fill="white"
                  stroke="var(--color-primary, #6366f1)"
                  strokeWidth={isHovered ? 2.5 : 2}
                  className="transition-all"
                />
              </g>
            )
          })}
        </svg>

        {/* Tooltip HTML sovrapposto */}
        {hoveredPoint && hoveredIndex !== null && points[hoveredIndex] && (
          <div
            className="pointer-events-none absolute z-20 rounded-md border border-border bg-ink text-surface px-2.5 py-1.5 shadow-lg text-xs"
            style={{
              left: `${(points[hoveredIndex].x / width) * 100}%`,
              top: `${(points[hoveredIndex].y / height) * 100}%`,
              transform: 'translate(-50%, -125%)',
            }}
          >
            <p className="font-semibold">{hoveredPoint.etichetta}</p>
            <p className="text-primary-soft font-mono font-bold">
              € {hoveredPoint.totale.toFixed(2)}
            </p>
            <p className="text-[10px] text-surface-alt/80">
              {hoveredPoint.appuntamenti} {hoveredPoint.appuntamenti === 1 ? 'appuntamento' : 'appuntamenti'}
            </p>
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-ink-muted border-t border-border pt-3">
        <span>
          Media giornaliera:{' '}
          <strong className="text-ink font-mono">€ {mediaGiornaliera.toFixed(2)}</strong>
        </span>
        <span>Passa il cursore sui punti per vedere i dettagli giornalieri</span>
      </div>
    </div>
  )
}
