import { useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { X } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { DataTable } from '@/components/data-table/data-table'
import { PageHeader } from '@/components/ui/page-header'
import { useToast } from '@/components/ui/toast'
import { ApiError } from '@/lib/api'

import { useCancellaPrenotazione, useLeMiePrenotazioni } from './hooks'
import type { Prenotazione } from './types'

const VARIANTE_STATO: Record<Prenotazione['stato'], 'success' | 'danger' | 'neutral'> = {
  confermata: 'success',
  cancellata: 'danger',
  completata: 'neutral',
}

const ETICHETTA_STATO: Record<Prenotazione['stato'], string> = {
  confermata: 'Confermata',
  cancellata: 'Cancellata',
  completata: 'Completata',
}

const ETICHETTA_PAGAMENTO: Record<Prenotazione['stato_pagamento'], string> = {
  pagato: 'Pagato',
  non_pagato: 'Da pagare',
}

export function LeMiePrenotazioniPage() {
  const [pagina, setPagina] = useState(1)
  const [daCancellare, setDaCancellare] = useState<Prenotazione | null>(null)
  const { data, isLoading } = useLeMiePrenotazioni(pagina)
  const cancellaMutation = useCancellaPrenotazione()
  const { showToast } = useToast()

  const confermaCancellazione = async () => {
    if (!daCancellare) return
    try {
      await cancellaMutation.mutateAsync(daCancellare.id)
      showToast('Prenotazione cancellata.')
    } catch (error) {
      const messaggio =
        error instanceof ApiError && error.status === 400
          ? 'Fuori dai termini per cancellare online: contatta il salone.'
          : 'Errore imprevisto, riprova.'
      showToast(messaggio, 'error')
    } finally {
      setDaCancellare(null)
    }
  }

  const columns: ColumnDef<Prenotazione, unknown>[] = [
    {
      accessorKey: 'inizio',
      header: 'Quando',
      cell: ({ row }) =>
        new Date(row.original.inizio).toLocaleString('it-IT', {
          dateStyle: 'medium',
          timeStyle: 'short',
        }),
    },
    {
      accessorKey: 'stato',
      header: 'Stato',
      cell: ({ row }) => (
        <Badge variant={VARIANTE_STATO[row.original.stato]}>
          {ETICHETTA_STATO[row.original.stato]}
        </Badge>
      ),
    },
    {
      id: 'pagamento',
      header: 'Pagamento',
      cell: ({ row }) => (
        <span className="text-sm text-ink-muted">
          € {row.original.importo} · {ETICHETTA_PAGAMENTO[row.original.stato_pagamento]}
        </span>
      ),
    },
    { accessorKey: 'note', header: 'Note' },
    {
      id: 'azioni',
      header: '',
      cell: ({ row }) =>
        row.original.stato === 'confermata' ? (
          <div className="flex justify-end">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Cancella prenotazione"
              onClick={() => setDaCancellare(row.original)}
            >
              <X className="h-4 w-4 text-danger" />
            </Button>
          </div>
        ) : null,
    },
  ]

  return (
    <div>
      <PageHeader title="Le mie prenotazioni" description="Storico e prossimi appuntamenti." />

      <DataTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyTitle="Nessuna prenotazione"
        emptyDescription="Vai su “Prenota” per fissare il tuo primo appuntamento."
        pagination={
          data
            ? { page: pagina, totalCount: data.count, pageSize: 25, onPageChange: setPagina }
            : undefined
        }
      />

      <ConfirmDialog
        open={!!daCancellare}
        onOpenChange={(open) => !open && setDaCancellare(null)}
        title="Cancellare la prenotazione?"
        description="Se sei entro i termini di preavviso, la cancellazione è gratuita."
        destructive
        isLoading={cancellaMutation.isPending}
        onConfirm={confermaCancellazione}
      />
    </div>
  )
}
