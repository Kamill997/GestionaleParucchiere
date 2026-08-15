import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PageHeader } from '@/components/ui/page-header'
import { Select } from '@/components/ui/select'
import { useToast } from '@/components/ui/toast'
import { useOperatori } from '@/features/operatori/hooks'
import { useServizi } from '@/features/servizi/hooks'
import { ApiError } from '@/lib/api'
import { cn } from '@/lib/utils'

import { useCreaPrenotazione, useSlotDisponibili } from './hooks'
import type { SlotDisponibile } from './types'

const formattaOra = (iso: string) =>
  new Date(iso).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })

function domaniISO() {
  const domani = new Date()
  domani.setDate(domani.getDate() + 1)
  return domani.toISOString().slice(0, 10)
}

export function PrenotaPage() {
  const [servizioId, setServizioId] = useState('')
  const [operatoreId, setOperatoreId] = useState('')
  const [data, setData] = useState(domaniISO())
  const [slotScelto, setSlotScelto] = useState<SlotDisponibile | null>(null)

  const { data: servizi } = useServizi(1)
  const { data: operatori } = useOperatori(1, true)
  const {
    data: slot,
    isLoading: caricandoSlot,
    isFetching: aggiornandoSlot,
  } = useSlotDisponibili(operatoreId, servizioId, data)
  const creaMutation = useCreaPrenotazione()
  const { showToast } = useToast()

  const prontoPerScegliereData = !!servizioId && !!operatoreId

  const confermaPrenotazione = async () => {
    if (!slotScelto) return
    try {
      await creaMutation.mutateAsync({
        operatore: operatoreId,
        servizio: servizioId,
        inizio: slotScelto.inizio,
      })
      showToast('Prenotazione confermata!')
      setSlotScelto(null)
    } catch (error) {
      const messaggio =
        error instanceof ApiError && error.status === 400
          ? 'Questo slot non è più disponibile: scegline un altro.'
          : 'Errore imprevisto, riprova.'
      showToast(messaggio, 'error')
    }
  }

  return (
    <div>
      <PageHeader
        title="Prenota un appuntamento"
        description="Scegli servizio, operatore e orario."
      />

      <div className="grid max-w-2xl gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="servizio">Servizio</Label>
          <Select
            id="servizio"
            value={servizioId}
            onChange={(e) => {
              setServizioId(e.target.value)
              setSlotScelto(null)
            }}
          >
            <option value="">Seleziona un servizio…</option>
            {servizi?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nome} — {s.durata_minuti} min — € {s.prezzo}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Label htmlFor="operatore">Operatore</Label>
          <Select
            id="operatore"
            value={operatoreId}
            onChange={(e) => {
              setOperatoreId(e.target.value)
              setSlotScelto(null)
            }}
          >
            <option value="">Seleziona un operatore…</option>
            {operatori?.results.map((o) => (
              <option key={o.id} value={o.id}>
                {o.nome}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Label htmlFor="data">Giorno</Label>
          <Input
            id="data"
            type="date"
            min={new Date().toISOString().slice(0, 10)}
            value={data}
            onChange={(e) => {
              setData(e.target.value)
              setSlotScelto(null)
            }}
          />
        </div>
      </div>

      <div className="mt-6 max-w-2xl">
        {!prontoPerScegliereData ? (
          <p className="text-sm text-ink-muted">
            Scegli servizio e operatore per vedere gli orari liberi.
          </p>
        ) : caricandoSlot ? (
          <p className="text-sm text-ink-muted">Caricamento orari…</p>
        ) : slot && slot.length === 0 ? (
          <EmptyState
            title="Nessuno slot libero"
            description="Prova un altro giorno o un altro operatore."
          />
        ) : (
          <div>
            <p className="mb-2 text-sm font-medium text-ink">
              Orari liberi {aggiornandoSlot && '(aggiornamento…)'}
            </p>
            <div className="flex flex-wrap gap-2">
              {slot?.map((s) => (
                <button
                  key={s.inizio}
                  onClick={() => setSlotScelto(s)}
                  className={cn(
                    'rounded-md border px-3 py-2 text-sm font-medium transition-colors',
                    slotScelto?.inizio === s.inizio
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border bg-surface text-ink hover:border-primary',
                  )}
                >
                  {formattaOra(s.inizio)}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {slotScelto && (
        <div className="mt-6 max-w-2xl rounded-lg border border-border bg-surface-alt p-4">
          <p className="text-sm text-ink">
            Confermi l'appuntamento delle <strong>{formattaOra(slotScelto.inizio)}</strong> del{' '}
            <strong>{new Date(data).toLocaleDateString('it-IT')}</strong>?
          </p>
          <Button className="mt-3" onClick={confermaPrenotazione} disabled={creaMutation.isPending}>
            {creaMutation.isPending ? 'Conferma in corso…' : 'Conferma prenotazione'}
          </Button>
        </div>
      )}
    </div>
  )
}
