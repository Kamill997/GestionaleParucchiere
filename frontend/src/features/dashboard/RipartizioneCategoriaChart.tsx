import { useMemo, useState } from 'react'
import { PieChart as PieIcon } from 'lucide-react'

import type { CategoriaFatturato } from './hooks'

interface Props {
  categorie: CategoriaFatturato[]
  totalePeriodo: number
}

const COLORI_PALETTE = [
  '#6366f1', // Indigo
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#ec4899', // Pink
  '#0ea5e9', // Sky
  '#8b5cf6', // Violet
  '#14b8a6', // Teal
]

export function RipartizioneCategoriaChart({ categorie, totalePeriodo }: Props) {
  const [hoveredCategoria, setHoveredCategoria] = useState<CategoriaFatturato | null>(null)

  // Calcolo archi per grafico donut SVG
  const size = 220
  const center = size / 2
  const rOuter = 85
  const rInner = 52

  const slices = useMemo(() => {
    if (categorie.length === 0 || totalePeriodo <= 0) return []

    let currentAngle = -Math.PI / 2 // Inizia in alto (ore 12)

    return categorie.map((cat, idx) => {
      const angle = (cat.totale / totalePeriodo) * 2 * Math.PI
      const startAngle = currentAngle
      const endAngle = currentAngle + angle
      currentAngle = endAngle

      const x1 = center + rOuter * Math.cos(startAngle)
      const y1 = center + rOuter * Math.sin(startAngle)
      const x2 = center + rOuter * Math.cos(endAngle)
      const y2 = center + rOuter * Math.sin(endAngle)

      const x3 = center + rInner * Math.cos(endAngle)
      const y3 = center + rInner * Math.sin(endAngle)
      const x4 = center + rInner * Math.cos(startAngle)
      const y4 = center + rInner * Math.sin(startAngle)

      const largeArc = angle > Math.PI ? 1 : 0

      const d = [
        `M ${x1} ${y1}`,
        `A ${rOuter} ${rOuter} 0 ${largeArc} 1 ${x2} ${y2}`,
        `L ${x3} ${y3}`,
        `A ${rInner} ${rInner} 0 ${largeArc} 0 ${x4} ${y4}`,
        'Z',
      ].join(' ')

      const color = COLORI_PALETTE[idx % COLORI_PALETTE.length]

      return { d, cat, color, idx }
    })
  }, [categorie, totalePeriodo, center, rOuter, rInner])

  return (
    <div className="rounded-lg border border-border bg-surface p-5 shadow-sm flex flex-col justify-between">
      <div className="border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <PieIcon className="h-5 w-5 text-primary" />
          <h3 className="font-display text-base font-semibold text-ink">
            Ripartizione per Trattamento
          </h3>
        </div>
        <p className="text-xs text-ink-muted mt-0.5">
          Percentuale del fatturato per ciascuna categoria di servizio.
        </p>
      </div>

      {categorie.length === 0 ? (
        <p className="text-sm text-ink-muted py-12 text-center">Nessun dato registrato nel periodo.</p>
      ) : (
        <div className="mt-4 flex flex-col sm:flex-row items-center gap-6">
          {/* Donut SVG */}
          <div className="relative shrink-0">
            <svg width={size} height={size} className="overflow-visible select-none">
              {slices.map((s) => {
                const isHovered = hoveredCategoria?.categoria === s.cat.categoria
                return (
                  <path
                    key={s.cat.categoria}
                    d={s.d}
                    fill={s.color}
                    opacity={hoveredCategoria ? (isHovered ? 1 : 0.45) : 0.9}
                    stroke="var(--color-surface, #ffffff)"
                    strokeWidth={isHovered ? 3 : 1.5}
                    className="cursor-pointer transition-all hover:opacity-100"
                    onMouseEnter={() => setHoveredCategoria(s.cat)}
                    onMouseLeave={() => setHoveredCategoria(null)}
                  />
                )
              })}
            </svg>

            {/* Testo centrale donut */}
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
              {hoveredCategoria ? (
                <>
                  <span className="text-xs font-semibold text-ink truncate max-w-[90px]">
                    {hoveredCategoria.categoria}
                  </span>
                  <span className="font-mono text-base font-bold text-primary">
                    {hoveredCategoria.percentuale}%
                  </span>
                  <span className="text-[10px] text-ink-muted">
                    € {hoveredCategoria.totale.toFixed(0)}
                  </span>
                </>
              ) : (
                <>
                  <span className="text-[10px] uppercase tracking-wider text-ink-muted">
                    Totale
                  </span>
                  <span className="font-mono text-base font-bold text-ink">
                    € {totalePeriodo.toFixed(0)}
                  </span>
                  <span className="text-[10px] text-ink-muted">
                    {categorie.reduce((acc, c) => acc + c.appuntamenti, 0)} prenotazioni
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Legenda con percentuali */}
          <div className="w-full space-y-2">
            {categorie.map((cat, idx) => {
              const color = COLORI_PALETTE[idx % COLORI_PALETTE.length]
              const isHovered = hoveredCategoria?.categoria === cat.categoria
              return (
                <div
                  key={cat.categoria}
                  onMouseEnter={() => setHoveredCategoria(cat)}
                  onMouseLeave={() => setHoveredCategoria(null)}
                  className={`flex items-center justify-between p-1.5 rounded text-xs transition-colors cursor-pointer ${
                    isHovered ? 'bg-surface-alt font-semibold' : 'hover:bg-surface-alt/60'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <span
                      className="h-3 w-3 rounded-xs shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <span className="truncate text-ink">{cat.categoria}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 font-mono">
                    <span className="text-ink-muted">€ {cat.totale.toFixed(2)}</span>
                    <span className="w-11 text-right font-bold text-primary">
                      {cat.percentuale}%
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
