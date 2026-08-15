import { useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { Check, UserX, X } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { DataTable } from '@/components/data-table/data-table'
import { PageHeader } from '@/components/ui/page-header'
import { Select } from '@/components/ui/select'
import { useToast } from '@/components/ui/toast'

import {
  useAggiornaPagamento,
  useCancellaPrenotazione,
  useSegnaPresenza,
  useTuttePrenotazioni,
} from './hooks'
import type { Prenotazione } from './types'

const VARIANTE_STATO: Record<Prenotazione['stato'], 'success' | 'danger' | 'neutral'> = {
  confermata: 'success',
  cancellata: 'danger',
  completata: 'neutral',
}

const VARIANTE_PAGAMENTO: Record<Prenotazione['stato_pagamento'], 'success' | 'warning'> = {
  pagato: 'success',
  non_pagato: 'warning',
}

const VARIANTE_PRESENZA: Record<Prenotazione['stato_presenza'], 'neutral' | 'success' | 'danger'> =
  {
    da_verificare: 'neutral',
    presente: 'success',
    non_presente: 'danger',
  }

function formattaDataOra(iso: string) {
  return new Date(iso).toLocaleString('it-IT', { dateStyle: 'short', timeStyle: 'short' })
}

export function GestionePrenotazioniPage() {
  const [pagina, setPagina] = useState(1)
  const [filtroStato, setFiltroStato] = useState('')
  const [daCancellare, setDaCancellare] = useState<Prenotazione | null>(null)

  const { data, isLoading } = useTuttePrenotazioni(pagina, filtroStato || undefined)
  const segnaPresenzaMutation = useSegnaPresenza()
  const aggiornaPagamentoMutation = useAggiornaPagamento()
  const cancellaMutation = useCancellaPrenotazione()
  const { showToast } = useToast()

  const toggleFatturato = async (prenotazione: Prenotazione) => {
    try {
      await aggiornaPagamentoMutation.mutateAsync({
        id: prenotazione.id,
        stato_pagamento: prenotazione.stato_pagamento === 'pagato' ? 'non_pagato' : 'pagato',
      })
    } catch {
      showToast('Errore aggiornando il pagamento.', 'error')
    }
  }

  const marcaPresenza = async (prenotazione: Prenotazione, presente: boolean) => {
    try {
      await segnaPresenzaMutation.mutateAsync({
        id: prenotazione.id,
        stato_presenza: presente ? 'presente' : 'non_presente',
      })
      if (!presente) showToast('Segnato come non presentato.')
    } catch {
      showToast('Errore segnando la presenza.', 'error')
    }
  }

  const confermaCancellazione = async () => {
    if (!daCancellare) return
    try {
      await cancellaMutation.mutateAsync(daCancellare.id)
      showToast('Prenotazione cancellata.')
    } catch {
      showToast('Errore imprevisto, riprova.', 'error')
    } finally {
      setDaCancellare(null)
    }
  }

  const columns: ColumnDef<Prenotazione, unknown>[] = [
    {
      accessorKey: 'inizio',
      header: 'Quando',
      cell: ({ row }) => formattaDataOra(row.original.inizio),
    },
    { accessorKey: 'cliente_nome', header: 'Cliente' },
    { accessorKey: 'operatore_nome', header: 'Operatore' },
    { accessorKey: 'servizio_nome', header: 'Servizio' },
    {
      accessorKey: 'stato',
      header: 'Stato',
      cell: ({ row }) => (
        <Badge variant={VARIANTE_STATO[row.original.stato]}>{row.original.stato}</Badge>
      ),
    },
    {
      id: 'pagamento',
      header: 'Pagamento',
      cell: ({ row }) => (
        <button
          onClick={() => toggleFatturato(row.original)}
          disabled={row.original.stato === 'cancellata'}
          className="disabled:opacity-40"
        >
          <Badge variant={VARIANTE_PAGAMENTO[row.original.stato_pagamento]}>
            € {row.original.importo} ·{' '}
            {row.original.stato_pagamento === 'pagato' ? 'Pagato' : 'Da pagare'}
          </Badge>
        </button>
      ),
    },
    {
      id: 'presenza',
      header: 'Presenza',
      cell: ({ row }) =>
        row.original.stato === 'cancellata' ? null : (
          <div className="flex items-center gap-2">
            <Badge variant={VARIANTE_PRESENZA[row.original.stato_presenza]}>
              {row.original.stato_presenza.replace('_', ' ')}
            </Badge>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Segna presente"
              onClick={() => marcaPresenza(row.original, true)}
            >
              <Check className="h-4 w-4 text-success" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Segna non presente"
              onClick={() => marcaPresenza(row.original, false)}
            >
              <UserX className="h-4 w-4 text-danger" />
            </Button>
          </div>
        ),
    },
    {
      id: 'azioni',
      header: '',
      cell: ({ row }) =>
        row.original.stato === 'confermata' ? (
          <Button
            variant="ghost"
            size="icon"
            aria-label="Cancella"
            onClick={() => setDaCancellare(row.original)}
          >
            <X className="h-4 w-4 text-danger" />
          </Button>
        ) : null,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Gestione prenotazioni"
        description="Tutti gli appuntamenti: pagamento, presenza, cancellazione."
        actions={
          <Select
            value={filtroStato}
            onChange={(e) => setFiltroStato(e.target.value)}
            className="w-40"
          >
            <option value="">Tutti gli stati</option>
            <option value="confermata">Confermata</option>
            <option value="cancellata">Cancellata</option>
            <option value="completata">Completata</option>
          </Select>
        }
      />

      <DataTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyTitle="Nessuna prenotazione"
        pagination={
          data
            ? { page: pagina, totalCount: data.count, pageSize: 25, onPageChange: setPagina }
            : undefined
        }
      />

      <ConfirmDialog
        open={!!daCancellare}
        onOpenChange={(open) => !open && setDaCancellare(null)}
        title="Cancellare questa prenotazione?"
        destructive
        isLoading={cancellaMutation.isPending}
        onConfirm={confermaCancellazione}
      />
    </div>
  )
}
