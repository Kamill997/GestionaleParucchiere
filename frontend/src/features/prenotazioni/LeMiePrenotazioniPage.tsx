import { useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { Bell, Calendar, CalendarDays, ExternalLink, X } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { DataTable } from '@/components/data-table/data-table'
import { PageHeader } from '@/components/ui/page-header'
import { useToast } from '@/components/ui/toast'
import { ApiError } from '@/lib/api'

import { generaGoogleCalendarUrl, scaricaFileIcs } from './calendarUtils'
import { useCancellaPrenotazione, useLeMiePrenotazioni } from './hooks'
import { ListaAttesaTable } from './ListaAttesaTable'
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
  const [vista, setVista] = useState<'appuntamenti' | 'lista_attesa'>('appuntamenti')
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
      id: 'servizio',
      header: 'Trattamenti',
      cell: ({ row }) => {
        const extra = row.original.servizi_aggiuntivi_dettaglio
        return (
          <div>
            <span className="font-medium text-ink">{row.original.servizio_nome}</span>
            {extra && extra.length > 0 && (
              <p className="text-xs text-primary font-medium">
                + {extra.map((e) => e.nome).join(', ')}
              </p>
            )}
            <p className="text-[11px] text-ink-muted">con {row.original.operatore_nome}</p>
          </div>
        )
      },
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
          <div className="flex justify-end gap-1">
            <Button
              variant="ghost"
              size="icon"
              title="Scarica file iCal (.ics)"
              aria-label="Scarica file iCal"
              onClick={async () => {
                try {
                  await scaricaFileIcs(row.original.id)
                } catch {
                  showToast('Impossibile scaricare il file calendario', 'error')
                }
              }}
            >
              <Calendar className="h-4 w-4 text-primary" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              asChild
              title="Aggiungi a Google Calendar"
              aria-label="Aggiungi a Google Calendar"
            >
              <a
                href={generaGoogleCalendarUrl(row.original)}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="h-4 w-4 text-ink-muted hover:text-primary" />
              </a>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Cancella prenotazione"
              title="Cancella prenotazione"
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
      <PageHeader
        title="Le mie prenotazioni"
        description="Storico, prossimi appuntamenti e richieste in lista d'attesa."
        actions={
          <div className="flex rounded-md border border-border bg-surface-hover/50 p-0.5">
            <button
              type="button"
              onClick={() => setVista('appuntamenti')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-all ${
                vista === 'appuntamenti'
                  ? 'bg-surface text-primary shadow-xs font-semibold'
                  : 'text-ink-muted hover:text-ink'
              }`}
            >
              <CalendarDays className="h-3.5 w-3.5" />
              <span>Appuntamenti</span>
            </button>
            <button
              type="button"
              onClick={() => setVista('lista_attesa')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-all ${
                vista === 'lista_attesa'
                  ? 'bg-surface text-primary shadow-xs font-semibold'
                  : 'text-ink-muted hover:text-ink'
              }`}
            >
              <Bell className="h-3.5 w-3.5" />
              <span>Lista d'attesa</span>
            </button>
          </div>
        }
      />

      {vista === 'appuntamenti' ? (
        <>
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
        </>
      ) : (
        <ListaAttesaTable isStaff={false} />
      )}
    </div>
  )
}
