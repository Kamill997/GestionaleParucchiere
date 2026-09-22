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
  const [filtroRuolo, setFiltroRuolo] = useState<'staff' | 'clienti' | 'tutti'>('staff')
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

  const utentiFiltrati = (data?.results ?? []).filter((u) => {
    const eStaff = u.ruoli.some((r) => r === 'Amministratore' || r === 'Operatore')
    if (filtroRuolo === 'staff') return eStaff
    if (filtroRuolo === 'clienti') return !eStaff
    return true
  })

  return (
    <div>
      <PageHeader
        title="Utenti e ruoli"
        description="Gestione delle credenziali e dei permessi di accesso per il personale del salone."
        actions={
          <Button onClick={apriPerCreazione}>
            <Plus className="h-4 w-4" />
            Nuovo utente staff
          </Button>
        }
      />

      <div className="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex rounded-md border border-border bg-surface p-1">
          <button
            type="button"
            onClick={() => setFiltroRuolo('staff')}
            className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              filtroRuolo === 'staff'
                ? 'bg-primary text-white shadow-xs font-semibold'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            Personale & Staff ({ (data?.results ?? []).filter((u) => u.ruoli.some((r) => r === 'Amministratore' || r === 'Operatore')).length })
          </button>
          <button
            type="button"
            onClick={() => setFiltroRuolo('clienti')}
            className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              filtroRuolo === 'clienti'
                ? 'bg-primary text-white shadow-xs font-semibold'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            Clienti registrati ({ (data?.results ?? []).filter((u) => !u.ruoli.some((r) => r === 'Amministratore' || r === 'Operatore')).length })
          </button>
          <button
            type="button"
            onClick={() => setFiltroRuolo('tutti')}
            className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              filtroRuolo === 'tutti'
                ? 'bg-primary text-white shadow-xs font-semibold'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            Tutti ({ data?.results?.length ?? 0 })
          </button>
        </div>

        <p className="text-xs text-ink-muted">
          {filtroRuolo === 'staff'
            ? 'Stai visualizzando solo gli account del personale con accesso gestionale.'
            : filtroRuolo === 'clienti'
            ? 'Questi utenti sono clienti che usano la PWA per prenotare. L\'anagrafica completa con note è in "Clienti".'
            : 'Visualizzazione completa di tutti gli account nel database.'}
        </p>
      </div>

      <DataTable
        columns={columns}
        data={utentiFiltrati}
        isLoading={isLoading}
        emptyTitle="Nessun utente trovato per questa selezione"
        pagination={
          data
            ? { page: pagina, totalCount: utentiFiltrati.length, pageSize: 100, onPageChange: setPagina }
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
