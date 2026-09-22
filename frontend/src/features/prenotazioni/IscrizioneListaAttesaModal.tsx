import { useState } from 'react'
import { Bell, Clock } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/components/ui/toast'
import { formattaErroreApi } from '@/lib/api'

import { useIscrivitiListaAttesa } from './hooks'

interface IscrizioneListaAttesaModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  servizioId: string
  servizioNome: string
  operatoreId?: string
  operatoreNome?: string
  data: string
  oraIniziale?: string
  onSuccess?: () => void
}

export function IscrizioneListaAttesaModal({
  open,
  onOpenChange,
  servizioId,
  servizioNome,
  operatoreId,
  operatoreNome,
  data,
  oraIniziale,
  onSuccess,
}: IscrizioneListaAttesaModalProps) {
  const [oraPreferita, setOraPreferita] = useState(oraIniziale || '')
  const [note, setNote] = useState('')
  const [errore, setErrore] = useState<string | null>(null)

  const iscrivitiMutation = useIscrivitiListaAttesa()
  const { showToast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrore(null)

    if (!servizioId || !data) {
      setErrore('Servizio e data sono obbligatori.')
      return
    }

    try {
      await iscrivitiMutation.mutateAsync({
        servizio: servizioId,
        operatore: operatoreId || undefined,
        data,
        ora_preferita: oraPreferita ? (oraPreferita.length === 5 ? `${oraPreferita}:00` : oraPreferita) : undefined,
        note: note.trim() || undefined,
      })

      showToast("Sei in lista d'attesa! Ti avviseremo appena si libera un posto.")
      onOpenChange(false)
      onSuccess?.()
    } catch (err) {
      setErrore(formattaErroreApi(err, "Si è verificato un errore durante l'iscrizione. Riprova."))
    }
  }

  const dataFormattata = data
    ? new Date(`${data}T00:00:00`).toLocaleDateString('it-IT', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      })
    : ''

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        title="Iscriviti alla Lista d'Attesa"
        description="Se un appuntamento per questo servizio si libera o viene cancellato, riceverai una notifica immediata con il link per prenotare prima di chiunque altro."
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="rounded-lg border border-primary/20 bg-primary-surface/30 p-3 text-xs text-ink space-y-1">
            <div className="flex justify-between">
              <span className="text-ink-muted">Servizio:</span>
              <span className="font-semibold text-ink">{servizioNome || 'Non specificato'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-muted">Collaboratore:</span>
              <span className="font-medium text-ink">{operatoreNome || 'Qualsiasi collaboratore'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-muted">Data:</span>
              <span className="font-medium capitalize text-ink">{dataFormattata}</span>
            </div>
          </div>

          <div>
            <Label htmlFor="ora-preferita" className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-ink-muted" />
              <span>Orario preferito (facoltativo)</span>
            </Label>
            <Input
              id="ora-preferita"
              type="time"
              value={oraPreferita}
              onChange={(e) => setOraPreferita(e.target.value)}
              placeholder="es. 10:00"
            />
            <p className="mt-1 text-[11px] text-ink-muted">
              Se specifichi un orario, avrai priorità sulle cancellazioni per quell'ora specifica.
            </p>
          </div>

          <div>
            <Label htmlFor="note">Note o preferenze (facoltativo)</Label>
            <Textarea
              id="note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="es. Solo mattina, disponibile dalle 9 alle 12..."
              rows={2}
            />
          </div>

          {errore && (
            <div className="rounded-md bg-danger-surface p-2.5 text-xs text-danger font-medium border border-danger/30">
              {errore}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
              disabled={iscrivitiMutation.isPending}
            >
              Annulla
            </Button>
            <Button
              type="submit"
              disabled={iscrivitiMutation.isPending}
              className="gap-1.5"
            >
              <Bell className="h-4 w-4" />
              {iscrivitiMutation.isPending ? 'Iscrizione in corso…' : 'Iscriviti alla lista'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
