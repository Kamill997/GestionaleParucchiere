import { useState } from 'react'
import { CalendarOff, Palmtree, Plus, Trash2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { useToast } from '@/components/ui/toast'
import { formattaErroreApi } from '@/lib/api'

import { useCreaEccezione, useEliminaEccezione, useEccezioni } from './hooks'
import type { Operatore, TipoEccezione } from './types'

interface EccezioniOperatoreDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  operatore: Operatore | null
}

const ETICHETTA_TIPO: Record<TipoEccezione, { label: string; variant: 'warning' | 'danger' | 'neutral' | 'success' }> = {
  ferie: { label: 'Ferie', variant: 'warning' },
  malattia: { label: 'Malattia', variant: 'danger' },
  permesso: { label: 'Permesso', variant: 'neutral' },
  chiusura: { label: 'Chiusura salone', variant: 'danger' },
}

export function EccezioniOperatoreDialog({
  open,
  onOpenChange,
  operatore,
}: EccezioniOperatoreDialogProps) {
  const isChiusuraSalone = operatore === null

  // Query per recuperare le eccezioni
  const queryParams: Record<string, string> = isChiusuraSalone
    ? { salone: 'true' }
    : { operatore: operatore.id }

  const { data: eccezioniData, isLoading } = useEccezioni(open ? queryParams : undefined)
  const creaMutation = useCreaEccezione()
  const eliminaMutation = useEliminaEccezione()
  const { showToast } = useToast()

  // Stato form inserimento
  const [mostraForm, setMostraForm] = useState(false)
  const [tipo, setTipo] = useState<TipoEccezione>(isChiusuraSalone ? 'chiusura' : 'ferie')
  const [dataInizio, setDataInizio] = useState('')
  const [dataFine, setDataFine] = useState('')
  const [interaGiornata, setInteraGiornata] = useState(true)
  const [oraInizio, setOraInizio] = useState('09:00')
  const [oraFine, setOraFine] = useState('13:00')
  const [motivo, setMotivo] = useState('')

  const resetForm = () => {
    setTipo(isChiusuraSalone ? 'chiusura' : 'ferie')
    setDataInizio('')
    setDataFine('')
    setInteraGiornata(true)
    setOraInizio('09:00')
    setOraFine('13:00')
    setMotivo('')
    setMostraForm(false)
  }

  const handleCrea = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!dataInizio) {
      showToast('Seleziona almeno la data di inizio.', 'error')
      return
    }

    try {
      await creaMutation.mutateAsync({
        operatore: isChiusuraSalone ? null : operatore.id,
        tipo,
        data_inizio: dataInizio,
        data_fine: dataFine || dataInizio,
        ora_inizio: interaGiornata ? null : oraInizio,
        ora_fine: interaGiornata ? null : oraFine,
        motivo,
      })
      showToast('Eccezione registrata con successo.')
      resetForm()
    } catch (error) {
      showToast(formattaErroreApi(error, 'Errore durante il salvataggio.'), 'error')
    }
  }

  const handleElimina = async (id: string) => {
    try {
      await eliminaMutation.mutateAsync(id)
      showToast('Eccezione rimossa.')
    } catch (error) {
      showToast(formattaErroreApi(error, 'Impossibile rimuovere l\'eccezione.'), 'error')
    }
  }

  const listaEccezioni = eccezioniData?.results ?? []

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <div className="flex items-center gap-2 text-primary">
            {isChiusuraSalone ? (
              <CalendarOff className="h-5 w-5" />
            ) : (
              <Palmtree className="h-5 w-5" />
            )}
            <DialogTitle>
              {isChiusuraSalone
                ? 'Chiusure straordinarie del salone'
                : `Ferie e assenze — ${operatore.nome}`}
            </DialogTitle>
          </div>
          <p className="text-xs text-ink-muted">
            {isChiusuraSalone
              ? 'Configura festività o periodi di chiusura in cui l’intero salone non accetta prenotazioni.'
              : 'Configura i periodi di ferie, permessi o assenze per questo collaboratore.'}
          </p>
        </DialogHeader>

        <DialogBody className="space-y-4 py-2">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <span className="text-xs font-medium text-ink">
              {listaEccezioni.length} {listaEccezioni.length === 1 ? 'periodo registrato' : 'periodi registrati'}
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setMostraForm(!mostraForm)}
            >
              <Plus className="h-3.5 w-3.5" />
              <span>{mostraForm ? 'Annulla' : 'Aggiungi assenza'}</span>
            </Button>
          </div>

          {mostraForm && (
            <form onSubmit={handleCrea} className="rounded-lg border border-border bg-surface-alt/60 p-3.5 space-y-3">
              <h4 className="text-xs font-semibold text-ink uppercase tracking-wider">Nuovo periodo</h4>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <Label htmlFor="tipo" className="text-xs">Tipologia</Label>
                  <Select
                    id="tipo"
                    value={tipo}
                    onChange={(e) => setTipo(e.target.value as TipoEccezione)}
                    className="text-xs"
                  >
                    {!isChiusuraSalone && (
                      <>
                        <option value="ferie">Ferie</option>
                        <option value="permesso">Permesso</option>
                        <option value="malattia">Malattia</option>
                      </>
                    )}
                    <option value="chiusura">Chiusura salone</option>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="motivo" className="text-xs">Motivo / Descrizione</Label>
                  <Input
                    id="motivo"
                    placeholder="Es. Ferie estive, Corso"
                    value={motivo}
                    onChange={(e) => setMotivo(e.target.value)}
                    className="text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <Label htmlFor="data_inizio" className="text-xs">Dal giorno</Label>
                  <Input
                    id="data_inizio"
                    type="date"
                    required
                    value={dataInizio}
                    onChange={(e) => {
                      setDataInizio(e.target.value)
                      if (!dataFine) setDataFine(e.target.value)
                    }}
                    className="text-xs"
                  />
                </div>
                <div>
                  <Label htmlFor="data_fine" className="text-xs">Al giorno</Label>
                  <Input
                    id="data_fine"
                    type="date"
                    required
                    value={dataFine}
                    onChange={(e) => setDataFine(e.target.value)}
                    className="text-xs"
                  />
                </div>
              </div>

              <div className="space-y-2 pt-1 border-t border-border/60">
                <label className="flex items-center gap-2 text-xs font-medium text-ink cursor-pointer">
                  <input
                    type="checkbox"
                    checked={interaGiornata}
                    onChange={(e) => setInteraGiornata(e.target.checked)}
                    className="rounded border-border text-primary focus:ring-primary h-3.5 w-3.5"
                  />
                  <span>Tutto il giorno (nessun orario specifico)</span>
                </label>

                {!interaGiornata && (
                  <div className="grid grid-cols-2 gap-2.5 pt-1">
                    <div>
                      <Label htmlFor="ora_inizio" className="text-xs">Dalle ore</Label>
                      <Input
                        id="ora_inizio"
                        type="time"
                        value={oraInizio}
                        onChange={(e) => setOraInizio(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                    <div>
                      <Label htmlFor="ora_fine" className="text-xs">Alle ore</Label>
                      <Input
                        id="ora_fine"
                        type="time"
                        value={oraFine}
                        onChange={(e) => setOraFine(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={resetForm}
                >
                  Annulla
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={creaMutation.isPending}
                >
                  {creaMutation.isPending ? 'Salvataggio…' : 'Salva eccezione'}
                </Button>
              </div>
            </form>
          )}

          {isLoading ? (
            <div className="p-6 text-center text-xs text-ink-muted">Caricamento eccezioni…</div>
          ) : listaEccezioni.length === 0 ? (
            <div className="p-6 text-center text-xs text-ink-muted rounded-md border border-dashed border-border">
              Nessuna eccezione o chiusura registrata per questo periodo.
            </div>
          ) : (
            <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
              {listaEccezioni.map((ecc) => {
                const infoTipo = ETICHETTA_TIPO[ecc.tipo] ?? { label: ecc.tipo, variant: 'neutral' }
                const isSingoloGiorno = ecc.data_inizio === ecc.data_fine

                return (
                  <div
                    key={ecc.id}
                    className="flex items-center justify-between p-2.5 rounded-lg border border-border bg-surface hover:bg-surface-alt/40 transition-colors"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <Badge variant={infoTipo.variant} className="text-[10px] py-0">
                          {infoTipo.label}
                        </Badge>
                        <span className="text-xs font-semibold text-ink">
                          {isSingoloGiorno
                            ? new Date(ecc.data_inizio).toLocaleDateString('it-IT', { dateStyle: 'medium' })
                            : `${new Date(ecc.data_inizio).toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })} – ${new Date(ecc.data_fine).toLocaleDateString('it-IT', { dateStyle: 'medium' })}`}
                        </span>
                        {ecc.ora_inizio && ecc.ora_fine && (
                          <span className="text-[11px] text-ink-muted font-medium">
                            ({ecc.ora_inizio.slice(0, 5)} - {ecc.ora_fine.slice(0, 5)})
                          </span>
                        )}
                      </div>
                      {ecc.motivo && (
                        <p className="text-[11px] text-ink-muted truncate max-w-sm">
                          {ecc.motivo}
                        </p>
                      )}
                    </div>

                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleElimina(ecc.id)}
                      disabled={eliminaMutation.isPending}
                      className="text-danger hover:bg-danger-surface hover:text-danger h-7 w-7"
                      title="Rimuovi eccezione"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                )
              })}
            </div>
          )}
        </DialogBody>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Chiudi
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
