import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { ColumnDef } from '@tanstack/react-table'
import { Bell, Calendar, X } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { DataTable } from '@/components/data-table/data-table'
import { Select } from '@/components/ui/select'
import { useToast } from '@/components/ui/toast'
import { formattaErroreApi } from '@/lib/api'

import { useAnnullaRichiestaListaAttesa, useListaAttesa } from './hooks'
import type { RichiestaListaAttesa, StatoListaAttesa } from './types'

const VARIANTE_STATO: Record<StatoListaAttesa, 'warning' | 'success' | 'neutral' | 'danger'> = {
  in_attesa: 'warning',
  notificato: 'success',
  prenotato: 'neutral',
  annullato: 'danger',
}

const ETICHETTA_STATO: Record<StatoListaAttesa, string> = {
  in_attesa: 'In attesa',
  notificato: 'Posto disponibile!',
  prenotato: 'Prenotato',
  annullato: 'Annullato',
}

export function ListaAttesaTable({ isStaff = false }: { isStaff?: boolean }) {
  const [pagina, setPagina] = useState(1)
  const [filtroStato, setFiltroStato] = useState<string>('')
  const [daAnnullare, setDaAnnullare] = useState<RichiestaListaAttesa | null>(null)

  const { data, isLoading } = useListaAttesa(pagina, filtroStato || undefined)
  const annullaMutation = useAnnullaRichiestaListaAttesa()
  const { showToast } = useToast()

  const confermaAnnullamento = async () => {
    if (!daAnnullare) return
    try {
      await annullaMutation.mutateAsync(daAnnullare.id)
      showToast('Richiesta in lista d\'attesa annullata.')
    } catch (err) {
      showToast(formattaErroreApi(err, "Errore durante l'annullamento."), 'error')
    } finally {
      setDaAnnullare(null)
    }
  }

  const columns: ColumnDef<RichiestaListaAttesa, unknown>[] = [
    ...(isStaff
      ? [
          {
            accessorKey: 'cliente_nome' as const,
            header: 'Cliente',
            cell: ({ row }: { row: { original: RichiestaListaAttesa } }) => (
              <span className="font-medium text-ink">{row.original.cliente_nome}</span>
            ),
          },
        ]
      : []),
    {
      accessorKey: 'servizio_nome',
      header: 'Servizio',
      cell: ({ row }) => <span className="font-medium text-ink">{row.original.servizio_nome}</span>,
    },
    {
      accessorKey: 'operatore_nome',
      header: 'Collaboratore',
      cell: ({ row }) => (
        <span className="text-sm text-ink-muted">
          {row.original.operatore_nome || 'Qualsiasi'}
        </span>
      ),
    },
    {
      accessorKey: 'data',
      header: 'Data richiesta',
      cell: ({ row }) =>
        new Date(`${row.original.data}T00:00:00`).toLocaleDateString('it-IT', {
          weekday: 'short',
          day: 'numeric',
          month: 'short',
          year: 'numeric',
        }),
    },
    {
      accessorKey: 'ora_preferita',
      header: 'Orario preferito',
      cell: ({ row }) =>
        row.original.ora_preferita ? (
          <span className="text-sm text-ink">{row.original.ora_preferita.slice(0, 5)}</span>
        ) : (
          <span className="text-xs text-ink-muted">Qualsiasi</span>
        ),
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
      accessorKey: 'note',
      header: 'Note',
      cell: ({ row }) => (
        <span className="max-w-xs truncate text-xs text-ink-muted" title={row.original.note || ''}>
          {row.original.note || '-'}
        </span>
      ),
    },
    {
      id: 'azioni',
      header: '',
      cell: ({ row }) => {
        const item = row.original
        const puoAnnullare = item.stato === 'in_attesa' || item.stato === 'notificato'
        const eNotificato = item.stato === 'notificato'

        return (
          <div className="flex items-center justify-end gap-2">
            {!isStaff && eNotificato && (
              <Button size="sm" asChild className="gap-1 bg-success hover:bg-success/90 text-xs">
                <Link
                  to={`/prenota?servizio=${item.servizio}&operatore=${item.operatore || ''}&data=${item.data}`}
                >
                  <Calendar className="h-3.5 w-3.5" />
                  Prenota subito
                </Link>
              </Button>
            )}

            {puoAnnullare && (
              <Button
                variant="ghost"
                size="icon"
                title="Annulla richiesta"
                aria-label="Annulla richiesta lista d'attesa"
                onClick={() => setDaAnnullare(item)}
              >
                <X className="h-4 w-4 text-danger" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-ink">Richieste in Lista d'Attesa</span>
        </div>
        <Select
          value={filtroStato}
          onChange={(e) => setFiltroStato(e.target.value)}
          className="w-40"
        >
          <option value="">Tutti gli stati</option>
          <option value="in_attesa">In attesa</option>
          <option value="notificato">Posto disponibile</option>
          <option value="prenotato">Prenotato</option>
          <option value="annullato">Annullato</option>
        </Select>
      </div>

      <DataTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyTitle="Nessuna richiesta in lista d'attesa"
        emptyDescription={
          isStaff
            ? 'Non ci sono al momento clienti in attesa per slot occupati.'
            : 'Quando trovi un orario occupato, puoi iscriverti alla lista d\'attesa per essere avvisato se si libera.'
        }
        pagination={
          data
            ? { page: pagina, totalCount: data.count, pageSize: 25, onPageChange: setPagina }
            : undefined
        }
      />

      <ConfirmDialog
        open={!!daAnnullare}
        onOpenChange={(open) => !open && setDaAnnullare(null)}
        title="Annullare la richiesta in lista d'attesa?"
        description="Non riceverai più notifiche se si libera un appuntamento per questo servizio e data."
        destructive
        isLoading={annullaMutation.isPending}
        onConfirm={confermaAnnullamento}
      />
    </div>
  )
}
