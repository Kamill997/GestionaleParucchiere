import { useEffect, useState } from 'react'
import { CalendarClock } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/toast'
import { formattaErroreApi } from '@/lib/api'

import { useDisponibilitaOperatore, useSalvaTurniSettimana } from './hooks'
import type { GiornoTurnoInput, Operatore } from './types'

const NOMI_GIORNI = [
  'Lunedì',
  'Martedì',
  'Mercoledì',
  'Giovedì',
  'Venerdì',
  'Sabato',
  'Domenica',
]

interface TurnoGiornoUI {
  giorno_settimana: number
  attivo: boolean
  ora_inizio: string
  ora_fine: string
}

interface TurniOperatoreDialogProps {
  operatore: Operatore | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TurniOperatoreDialog({ operatore, open, onOpenChange }: TurniOperatoreDialogProps) {
  const { data: disponibilitaPaginata, isLoading } = useDisponibilitaOperatore(operatore?.id ?? null)
  const salvaMutation = useSalvaTurniSettimana()
  const { showToast } = useToast()

  const [turni, setTurni] = useState<TurnoGiornoUI[]>(() =>
    NOMI_GIORNI.map((_, i) => ({
      giorno_settimana: i,
      attivo: i < 5, // default lun-ven
      ora_inizio: '09:00',
      ora_fine: '18:00',
    })),
  )

  useEffect(() => {
    if (!disponibilitaPaginata?.results) return

    const mappaDisponibilita = new Map<number, { inizio: string; fine: string }>()
    for (const d of disponibilitaPaginata.results) {
      mappaDisponibilita.set(d.giorno_settimana, {
        inizio: d.ora_inizio.slice(0, 5),
        fine: d.ora_fine.slice(0, 5),
      })
    }

    setTurni(
      NOMI_GIORNI.map((_, i) => {
        const d = mappaDisponibilita.get(i)
        return {
          giorno_settimana: i,
          attivo: !!d,
          ora_inizio: d?.inizio ?? '09:00',
          ora_fine: d?.fine ?? '18:00',
        }
      }),
    )
  }, [disponibilitaPaginata])

  const toggleGiorno = (giorno: number) => {
    setTurni((prev) =>
      prev.map((t) => (t.giorno_settimana === giorno ? { ...t, attivo: !t.attivo } : t)),
    )
  }

  const updateOrario = (giorno: number, campo: 'ora_inizio' | 'ora_fine', valore: string) => {
    setTurni((prev) =>
      prev.map((t) => (t.giorno_settimana === giorno ? { ...t, [campo]: valore } : t)),
    )
  }

  const handleSalva = async () => {
    if (!operatore) return

    // Validazione
    for (const t of turni) {
      if (t.attivo && t.ora_fine <= t.ora_inizio) {
        showToast(
          `L'orario di fine deve essere successivo all'inizio per ${NOMI_GIORNI[t.giorno_settimana]}.`,
          'error',
        )
        return
      }
    }

    const payloadGiorni: GiornoTurnoInput[] = turni
      .filter((t) => t.attivo)
      .map((t) => ({
        giorno_settimana: t.giorno_settimana,
        ora_inizio: `${t.ora_inizio}:00`,
        ora_fine: `${t.ora_fine}:00`,
      }))

    try {
      await salvaMutation.mutateAsync({
        operatoreId: operatore.id,
        giorni: payloadGiorni,
      })
      showToast('Turni settimanali aggiornati con successo!')
      onOpenChange(false)
    } catch (err) {
      showToast(formattaErroreApi(err, 'Errore durante il salvataggio dei turni.'), 'error')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <div className="flex items-center gap-2 text-primary">
            <CalendarClock className="h-5 w-5" />
            <DialogTitle>Turni di Lavoro — {operatore?.nome}</DialogTitle>
          </div>
          <DialogDescription>
            Configura le fasce orarie settimanali in cui questo operatore è disponibile per le prenotazioni.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="p-6 text-center text-sm text-ink-muted">Caricamento orari…</div>
        ) : (
          <div className="my-2 space-y-3">
            {turni.map((t) => (
              <div
                key={t.giorno_settimana}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface p-3"
              >
                <div className="flex items-center gap-3 w-32">
                  <input
                    type="checkbox"
                    id={`giorno-${t.giorno_settimana}`}
                    checked={t.attivo}
                    onChange={() => toggleGiorno(t.giorno_settimana)}
                    className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <label
                    htmlFor={`giorno-${t.giorno_settimana}`}
                    className={`text-sm font-medium cursor-pointer ${
                      t.attivo ? 'text-ink' : 'text-ink-muted line-through'
                    }`}
                  >
                    {NOMI_GIORNI[t.giorno_settimana]}
                  </label>
                </div>

                {t.attivo ? (
                  <div className="flex items-center gap-2">
                    <Input
                      type="time"
                      value={t.ora_inizio}
                      onChange={(e) => updateOrario(t.giorno_settimana, 'ora_inizio', e.target.value)}
                      className="h-8 w-28 text-sm"
                    />
                    <span className="text-xs text-ink-muted">alle</span>
                    <Input
                      type="time"
                      value={t.ora_fine}
                      onChange={(e) => updateOrario(t.giorno_settimana, 'ora_fine', e.target.value)}
                      className="h-8 w-28 text-sm"
                    />
                  </div>
                ) : (
                  <span className="text-xs text-ink-muted italic pr-4">Riposo settimanale</span>
                )}
              </div>
            ))}
          </div>
        )}

        <DialogFooter className="mt-4">
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Annulla
          </Button>
          <Button onClick={handleSalva} disabled={salvaMutation.isPending}>
            {salvaMutation.isPending ? 'Salvataggio…' : 'Salva turni'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
