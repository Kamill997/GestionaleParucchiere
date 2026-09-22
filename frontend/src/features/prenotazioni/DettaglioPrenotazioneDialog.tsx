import { useState } from 'react'
import { Calendar, Check, Euro, User, UserX, X } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import {
  Dialog,
  DialogBody,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/toast'

import {
  useAggiornaPagamento,
  useCancellaPrenotazione,
  useSegnaPresenza,
} from './hooks'
import type { Prenotazione } from './types'

interface DettaglioPrenotazioneDialogProps {
  prenotazione: Prenotazione | null
  onClose: () => void
}

function formattaDataOra(iso: string) {
  return new Date(iso).toLocaleString('it-IT', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formattaOra(iso: string) {
  return new Date(iso).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
}

export function DettaglioPrenotazioneDialog({
  prenotazione,
  onClose,
}: DettaglioPrenotazioneDialogProps) {
  const [showConfirmCancel, setShowConfirmCancel] = useState(false)
  const { showToast } = useToast()

  const segnaPresenzaMutation = useSegnaPresenza()
  const aggiornaPagamentoMutation = useAggiornaPagamento()
  const cancellaMutation = useCancellaPrenotazione()

  if (!prenotazione) return null

  const handlePresenza = async (stato_presenza: 'presente' | 'non_presente') => {
    try {
      await segnaPresenzaMutation.mutateAsync({
        id: prenotazione.id,
        stato_presenza,
      })
      showToast(
        stato_presenza === 'presente' ? 'Presenza confermata!' : 'Segnato come non presente.',
      )
      onClose()
    } catch {
      showToast("Errore durante l'aggiornamento presenza", 'error')
    }
  }

  const handleTogglePagamento = async () => {
    try {
      const nuovoStato = prenotazione.stato_pagamento === 'pagato' ? 'non_pagato' : 'pagato'
      await aggiornaPagamentoMutation.mutateAsync({
        id: prenotazione.id,
        stato_pagamento: nuovoStato,
      })
      showToast(
        nuovoStato === 'pagato' ? 'Pagamento registrato!' : 'Stato pagamento reimpostato.',
      )
      onClose()
    } catch {
      showToast('Errore aggiornamento pagamento', 'error')
    }
  }

  const handleCancella = async () => {
    try {
      await cancellaMutation.mutateAsync(prenotazione.id)
      showToast('Prenotazione cancellata')
      setShowConfirmCancel(false)
      onClose()
    } catch {
      showToast('Errore cancellazione prenotazione', 'error')
    }
  }

  const isOpen = !!prenotazione

  return (
    <>
      <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle className="text-lg font-semibold text-ink">
                Dettaglio Prenotazione
              </DialogTitle>
              <DialogClose asChild>
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded p-1 text-ink-muted hover:bg-surface-hover"
                >
                  <X className="h-5 w-5" />
                </button>
              </DialogClose>
            </div>
          </DialogHeader>

          <DialogBody className="space-y-4 py-3">
            {/* Orario e Data */}
            <div className="flex items-center gap-2 text-sm text-ink font-medium bg-surface-hover/60 p-2.5 rounded-md">
              <Calendar className="h-4 w-4 text-primary" />
              <span>{formattaDataOra(prenotazione.inizio)} – {formattaOra(prenotazione.fine)}</span>
            </div>

            {/* Dati Servizio & Prezzo */}
            <div className="border border-border rounded-lg p-3 space-y-1.5 bg-surface">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium text-ink">{prenotazione.servizio_nome}</h4>
                </div>
                <span className="font-semibold text-primary">€ {prenotazione.importo}</span>
              </div>
              <div className="pt-1 text-xs text-ink-muted flex items-center gap-1.5">
                <User className="h-3.5 w-3.5" />
                <span>Operatrice: <strong>{prenotazione.operatore_nome}</strong></span>
              </div>
            </div>

            {/* Dati Cliente */}
            <div className="border border-border rounded-lg p-3 space-y-1.5 bg-surface">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">Cliente</h4>
              <p className="text-sm font-medium text-ink">{prenotazione.cliente_nome}</p>
              {prenotazione.note && (
                <p className="text-xs text-ink-muted pt-1">
                  <strong>Note:</strong> {prenotazione.note}
                </p>
              )}
            </div>

            {/* Stato & Badge */}
            <div className="flex flex-wrap gap-2 pt-1">
              <Badge
                variant={
                  prenotazione.stato === 'confermata'
                    ? 'success'
                    : prenotazione.stato === 'cancellata'
                      ? 'danger'
                      : 'neutral'
                }
              >
                {prenotazione.stato}
              </Badge>

              <Badge variant={prenotazione.stato_pagamento === 'pagato' ? 'success' : 'warning'}>
                {prenotazione.stato_pagamento === 'pagato' ? 'Pagato' : 'Da pagare'}
              </Badge>

              <Badge
                variant={
                  prenotazione.stato_presenza === 'presente'
                    ? 'success'
                    : prenotazione.stato_presenza === 'non_presente'
                      ? 'danger'
                      : 'neutral'
                }
              >
                {prenotazione.stato_presenza === 'presente'
                  ? 'Presente'
                  : prenotazione.stato_presenza === 'non_presente'
                    ? 'No-Show'
                    : 'Da verificare'}
              </Badge>
            </div>

            {/* Azioni Rapide per Staff */}
            <div className="border-t border-border pt-4 space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Azioni Rapide
              </p>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full justify-center text-xs"
                  onClick={() => handlePresenza('presente')}
                  disabled={prenotazione.stato_presenza === 'presente' || segnaPresenzaMutation.isPending}
                >
                  <Check className="h-3.5 w-3.5 mr-1 text-success" />
                  Segna Presente
                </Button>

                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full justify-center text-xs"
                  onClick={() => handlePresenza('non_presente')}
                  disabled={prenotazione.stato_presenza === 'non_presente' || segnaPresenzaMutation.isPending}
                >
                  <UserX className="h-3.5 w-3.5 mr-1 text-danger" />
                  Segna Assente
                </Button>

                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full justify-center text-xs"
                  onClick={handleTogglePagamento}
                  disabled={aggiornaPagamentoMutation.isPending}
                >
                  <Euro className="h-3.5 w-3.5 mr-1 text-primary" />
                  {prenotazione.stato_pagamento === 'pagato' ? 'Segna Non Pagato' : 'Segna Pagato'}
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-center text-xs text-danger hover:bg-danger-surface"
                  onClick={() => setShowConfirmCancel(true)}
                  disabled={prenotazione.stato === 'cancellata' || cancellaMutation.isPending}
                >
                  <X className="h-3.5 w-3.5 mr-1" />
                  Cancella
                </Button>
              </div>
            </div>
          </DialogBody>

          <DialogFooter>
            <Button variant="secondary" onClick={onClose} className="w-full">
              Chiudi
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={showConfirmCancel}
        onOpenChange={setShowConfirmCancel}
        title="Cancella prenotazione"
        description="Sei sicuro di voler cancellare questo appuntamento? Il cliente riceverà una notifica automatica."
        confirmLabel="Cancella appuntamento"
        destructive
        onConfirm={handleCancella}
        isLoading={cancellaMutation.isPending}
      />
    </>
  )
}
