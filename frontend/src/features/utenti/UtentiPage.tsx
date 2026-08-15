import { useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { Pencil, Plus } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/data-table/data-table'
import { FormModal, type CampoFormModal } from '@/components/form-modal/form-modal'
import { PageHeader } from '@/components/ui/page-header'
import { useToast } from '@/components/ui/toast'
import { ApiError } from '@/lib/api'

import { useAggiornaUtenteAdmin, useCreaUtenteAdmin, useUtentiAdmin } from './hooks'
import {
  utenteAdminCreateSchema,
  utenteAdminEditSchema,
  type UtenteAdminFormValues,
} from './schema'
import type { UtenteAdmin } from './types'

const RUOLI_DISPONIBILI = ['Cliente', 'Operatore', 'Amministratore']

const VARIANTE_STATO: Record<UtenteAdmin['stato'], 'success' | 'warning' | 'danger'> = {
  attivo: 'success',
  invitato: 'warning',
  sospeso: 'danger',
}

const CAMPI_BASE: CampoFormModal<UtenteAdminFormValues>[] = [
  { name: 'email', label: 'Email', type: 'email' },
  { name: 'nome', label: 'Nome', type: 'text' },
  { name: 'cognome', label: 'Cognome', type: 'text' },
  {
    name: 'stato',
    label: 'Stato',
    type: 'select',
    options: [
      { value: 'attivo', label: 'Attivo' },
      { value: 'invitato', label: 'Invitato' },
      { value: 'sospeso', label: 'Sospeso' },
    ],
  },
  {
    name: 'ruoli',
    label: 'Ruoli',
    type: 'checkbox-group',
    options: RUOLI_DISPONIBILI.map((r) => ({ value: r, label: r })),
  },
]

export function UtentiPage() {
  const [pagina, setPagina] = useState(1)
  const [utenteInModifica, setUtenteInModifica] = useState<UtenteAdmin | null>(null)
  const [modaleAperto, setModaleAperto] = useState(false)

  const { data, isLoading } = useUtentiAdmin(pagina)
  const creaMutation = useCreaUtenteAdmin()
  const aggiornaMutation = useAggiornaUtenteAdmin()
  const { showToast } = useToast()

  const campiForm: CampoFormModal<UtenteAdminFormValues>[] = [
    ...CAMPI_BASE,
    {
      name: 'password',
      label: utenteInModifica ? 'Nuova password (lascia vuoto per non cambiarla)' : 'Password',
      type: 'text',
    },
  ]

  const apriPerCreazione = () => {
    setUtenteInModifica(null)
    setModaleAperto(true)
  }

  const apriPerModifica = (utente: UtenteAdmin) => {
    setUtenteInModifica(utente)
    setModaleAperto(true)
  }

  const handleSubmit = async (valori: UtenteAdminFormValues) => {
    try {
      if (utenteInModifica) {
        const { password, ...resto } = valori
        await aggiornaMutation.mutateAsync({
          id: utenteInModifica.id,
          dati: password ? valori : resto,
        })
        showToast('Utente aggiornato.')
      } else {
        await creaMutation.mutateAsync(valori)
        showToast('Utente creato.')
      }
      setModaleAperto(false)
    } catch (error) {
      const messaggio =
        error instanceof ApiError
          ? "Controlla i dati inseriti (l'email potrebbe essere già in uso)."
          : 'Errore imprevisto, riprova.'
      showToast(messaggio, 'error')
    }
  }

  const columns: ColumnDef<UtenteAdmin, unknown>[] = [
    { accessorKey: 'email', header: 'Email' },
    {
      id: 'nome_completo',
      header: 'Nome',
      cell: ({ row }) => [row.original.nome, row.original.cognome].filter(Boolean).join(' ') || '—',
    },
    {
      accessorKey: 'ruoli',
      header: 'Ruoli',
      cell: ({ row }) => (
        <div className="flex flex-wrap gap-1">
          {row.original.ruoli.length > 0
            ? row.original.ruoli.map((r) => (
                <Badge key={r} variant="primary">
                  {r}
                </Badge>
              ))
            : '—'}
        </div>
      ),
    },
    {
      accessorKey: 'stato',
      header: 'Stato',
      cell: ({ row }) => (
        <Badge variant={VARIANTE_STATO[row.original.stato]}>{row.original.stato}</Badge>
      ),
    },
    {
      id: 'azioni',
      header: '',
      cell: ({ row }) => (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Modifica"
            onClick={() => apriPerModifica(row.original)}
          >
            <Pencil className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Utenti e ruoli"
        description="Account con accesso al gestionale."
        actions={
          <Button onClick={apriPerCreazione}>
            <Plus className="h-4 w-4" />
            Nuovo utente
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.results ?? []}
        isLoading={isLoading}
        emptyTitle="Nessun utente"
        pagination={
          data
            ? { page: pagina, totalCount: data.count, pageSize: 100, onPageChange: setPagina }
            : undefined
        }
      />

      <FormModal
        open={modaleAperto}
        onOpenChange={setModaleAperto}
        title={utenteInModifica ? 'Modifica utente' : 'Nuovo utente'}
        schema={utenteInModifica ? utenteAdminEditSchema : utenteAdminCreateSchema}
        fields={campiForm}
        defaultValues={utenteInModifica ?? { stato: 'attivo', ruoli: [] }}
        isSubmitting={creaMutation.isPending || aggiornaMutation.isPending}
        onSubmit={handleSubmit}
      />
    </div>
  )
}
