import { useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { Pencil, Plus, Trash2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { DataTable } from '@/components/data-table/data-table'
import { FormModal, type CampoFormModal } from '@/components/form-modal/form-modal'
import { PageHeader } from '@/components/ui/page-header'
import { useToast } from '@/components/ui/toast'
import { RoleGuard } from '@/features/auth/RoleGuard'
import { ApiError } from '@/lib/api'

import { useAggiornaServizio, useCreaServizio, useEliminaServizio, useServizi } from './hooks'
import { servizioSchema, type ServizioFormValues } from './schema'
import type { Servizio } from './types'

const CATEGORIE_SUGGERITE = ['Taglio', 'Colore', 'Trattamento', 'Barba']

const CAMPI_FORM: CampoFormModal<ServizioFormValues>[] = [
  { name: 'nome', label: 'Nome', type: 'text' },
  {
    name: 'categoria',
    label: 'Categoria',
    type: 'select',
    options: CATEGORIE_SUGGERITE.map((c) => ({ value: c, label: c })),
  },
  { name: 'descrizione', label: 'Descrizione', type: 'textarea' },
  { name: 'durata_minuti', label: 'Durata (minuti)', type: 'number' },
  { name: 'prezzo', label: 'Prezzo (€)', type: 'number' },
]

export function ServiziPage() {
  const [pagina, setPagina] = useState(1)
  const [servizioInModifica, setServizioInModifica] = useState<Servizio | null>(null)
  const [modaleAperto, setModaleAperto] = useState(false)
  const [servizioDaEliminare, setServizioDaEliminare] = useState<Servizio | null>(null)

  const { data, isLoading } = useServizi(pagina)
  const creaMutation = useCreaServizio()
  const aggiornaMutation = useAggiornaServizio()
  const eliminaMutation = useEliminaServizio()
  const { showToast } = useToast()

  const apriPerCreazione = () => {
    setServizioInModifica(null)
    setModaleAperto(true)
  }

  const apriPerModifica = (servizio: Servizio) => {
    setServizioInModifica(servizio)
    setModaleAperto(true)
  }

  const handleSubmit = async (valori: ServizioFormValues) => {
    try {
      if (servizioInModifica) {
        await aggiornaMutation.mutateAsync({ id: servizioInModifica.id, dati: valori })
        showToast('Servizio aggiornato.')
      } else {
        await creaMutation.mutateAsync(valori)
        showToast('Servizio creato.')
      }
      setModaleAperto(false)
    } catch (error) {
      const messaggio =
        error instanceof ApiError ? 'Controlla i dati inseriti.' : 'Errore imprevisto, riprova.'
      showToast(messaggio, 'error')
    }
  }

  const confermaEliminazione = async () => {
    if (!servizioDaEliminare) return
    try {
      await eliminaMutation.mutateAsync(servizioDaEliminare.id)
      showToast('Servizio eliminato.')
    } catch {
      showToast('Impossibile eliminare il servizio.', 'error')
    } finally {
      setServizioDaEliminare(null)
    }
  }

  const columns: ColumnDef<Servizio, unknown>[] = [
    { accessorKey: 'nome', header: 'Nome' },
    { accessorKey: 'categoria', header: 'Categoria' },
    {
      accessorKey: 'durata_minuti',
      header: 'Durata',
      cell: ({ row }) => `${row.original.durata_minuti} min`,
    },
    {
      accessorKey: 'prezzo',
      header: 'Prezzo',
      cell: ({ row }) => `€ ${row.original.prezzo}`,
    },
    {
      accessorKey: 'attivo',
      header: 'Stato',
      cell: ({ row }) => (
        <Badge variant={row.original.attivo ? 'success' : 'neutral'}>
          {row.original.attivo ? 'Attivo' : 'Disattivato'}
        </Badge>
      ),
    },
    {
      id: 'azioni',
      header: '',
      cell: ({ row }) => (
        <RoleGuard roles={['Amministratore']}>
          <div className="flex justify-end gap-1">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Modifica"
              onClick={() => apriPerModifica(row.original)}
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Elimina"
              onClick={() => setServizioDaEliminare(row.original)}
            >
              <Trash2 className="h-4 w-4 text-danger" />
            </Button>
          </div>
        </RoleGuard>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Servizi"
        description="Listino servizi del salone."
        actions={
          <RoleGuard roles={['Amministratore']}>
            <Button onClick={apriPerCreazione}>
              <Plus className="h-4 w-4" />
              Nuovo servizio
            </Button>
          </RoleGuard>
        }
      />

      <DataTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyTitle="Nessun servizio nel catalogo"
        emptyDescription="Aggiungi il primo servizio per iniziare a ricevere prenotazioni."
        pagination={
          data
            ? { page: pagina, totalCount: data.count, pageSize: 25, onPageChange: setPagina }
            : undefined
        }
      />

      <FormModal
        open={modaleAperto}
        onOpenChange={setModaleAperto}
        title={servizioInModifica ? 'Modifica servizio' : 'Nuovo servizio'}
        schema={servizioSchema}
        fields={CAMPI_FORM}
        defaultValues={servizioInModifica ?? { attivo: true }}
        isSubmitting={creaMutation.isPending || aggiornaMutation.isPending}
        onSubmit={handleSubmit}
      />

      <ConfirmDialog
        open={!!servizioDaEliminare}
        onOpenChange={(open) => !open && setServizioDaEliminare(null)}
        title="Eliminare questo servizio?"
        description={`"${servizioDaEliminare?.nome}" verrà rimosso dal catalogo. Le prenotazioni passate non vengono toccate.`}
        destructive
        isLoading={eliminaMutation.isPending}
        onConfirm={confermaEliminazione}
      />
    </div>
  )
}
