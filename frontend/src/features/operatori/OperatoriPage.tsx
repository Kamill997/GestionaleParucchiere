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
import { useUtentiAdmin } from '@/features/utenti/hooks'
import { ApiError } from '@/lib/api'

import { useAggiornaOperatore, useCreaOperatore, useEliminaOperatore, useOperatori } from './hooks'
import { operatoreSchema, type OperatoreFormValues } from './schema'
import type { Operatore } from './types'

export function OperatoriPage() {
  const [pagina, setPagina] = useState(1)
  const [operatoreInModifica, setOperatoreInModifica] = useState<Operatore | null>(null)
  const [modaleAperto, setModaleAperto] = useState(false)
  const [operatoreDaEliminare, setOperatoreDaEliminare] = useState<Operatore | null>(null)

  const { data, isLoading } = useOperatori(pagina)
  const { data: utenti } = useUtentiAdmin()
  const creaMutation = useCreaOperatore()
  const aggiornaMutation = useAggiornaOperatore()
  const eliminaMutation = useEliminaOperatore()
  const { showToast } = useToast()

  const campiForm: CampoFormModal<OperatoreFormValues>[] = [
    {
      name: 'user',
      label: 'Account collegato',
      type: 'select',
      options: utenti?.results.map((u) => ({ value: u.id, label: u.email })) ?? [],
    },
    { name: 'nome', label: 'Nome visualizzato', type: 'text' },
    {
      name: 'specializzazioni',
      label: 'Specializzazioni',
      type: 'text',
      placeholder: 'Es. Colore, Taglio uomo',
    },
  ]

  const apriPerCreazione = () => {
    setOperatoreInModifica(null)
    setModaleAperto(true)
  }

  const apriPerModifica = (operatore: Operatore) => {
    setOperatoreInModifica(operatore)
    setModaleAperto(true)
  }

  const handleSubmit = async (valori: OperatoreFormValues) => {
    try {
      if (operatoreInModifica) {
        await aggiornaMutation.mutateAsync({ id: operatoreInModifica.id, dati: valori })
        showToast('Operatore aggiornato.')
      } else {
        await creaMutation.mutateAsync(valori)
        showToast('Operatore creato.')
      }
      setModaleAperto(false)
    } catch (error) {
      const messaggio =
        error instanceof ApiError
          ? "Controlla i dati inseriti (l'account potrebbe essere già collegato a un altro operatore)."
          : 'Errore imprevisto, riprova.'
      showToast(messaggio, 'error')
    }
  }

  const confermaEliminazione = async () => {
    if (!operatoreDaEliminare) return
    try {
      await eliminaMutation.mutateAsync(operatoreDaEliminare.id)
      showToast('Operatore eliminato.')
    } catch (error) {
      const messaggio =
        error instanceof ApiError && error.status === 400
          ? 'Ha prenotazioni collegate: disattivalo invece di eliminarlo.'
          : 'Errore imprevisto, riprova.'
      showToast(messaggio, 'error')
    } finally {
      setOperatoreDaEliminare(null)
    }
  }

  const columns: ColumnDef<Operatore, unknown>[] = [
    { accessorKey: 'nome', header: 'Nome' },
    { accessorKey: 'email', header: 'Email account' },
    { accessorKey: 'specializzazioni', header: 'Specializzazioni' },
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
              onClick={() => setOperatoreDaEliminare(row.original)}
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
        title="Operatori"
        description="Staff del salone."
        actions={
          <RoleGuard roles={['Amministratore']}>
            <Button onClick={apriPerCreazione}>
              <Plus className="h-4 w-4" />
              Nuovo operatore
            </Button>
          </RoleGuard>
        }
      />

      <DataTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyTitle="Nessun operatore"
        emptyDescription="Aggiungi il primo operatore: serve un account utente già esistente da collegare."
        pagination={
          data
            ? { page: pagina, totalCount: data.count, pageSize: 25, onPageChange: setPagina }
            : undefined
        }
      />

      <FormModal
        open={modaleAperto}
        onOpenChange={setModaleAperto}
        title={operatoreInModifica ? 'Modifica operatore' : 'Nuovo operatore'}
        description={
          operatoreInModifica
            ? undefined
            : "L'account deve esistere già (creato via Django Admin finché non c'è il modulo Gestione Utenti)."
        }
        schema={operatoreSchema}
        fields={campiForm}
        defaultValues={operatoreInModifica ?? { attivo: true }}
        isSubmitting={creaMutation.isPending || aggiornaMutation.isPending}
        onSubmit={handleSubmit}
      />

      <ConfirmDialog
        open={!!operatoreDaEliminare}
        onOpenChange={(open) => !open && setOperatoreDaEliminare(null)}
        title="Eliminare questo operatore?"
        description={`"${operatoreDaEliminare?.nome}" verrà rimosso. Se ha prenotazioni collegate, disattivalo invece.`}
        destructive
        isLoading={eliminaMutation.isPending}
        onConfirm={confermaEliminazione}
      />
    </div>
  )
}
