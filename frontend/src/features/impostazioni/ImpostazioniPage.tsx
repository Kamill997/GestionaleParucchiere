import { useState } from 'react'
import { Check, Pencil, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { PageHeader } from '@/components/ui/page-header'
import { useToast } from '@/components/ui/toast'
import { ApiError } from '@/lib/api'

import { useAggiornaImpostazione, useImpostazioni } from './hooks'
import type { Impostazione } from './types'

function RigaImpostazione({
  impostazione,
  onSave,
}: {
  impostazione: Impostazione
  onSave: (id: string, valore: string) => Promise<void>
}) {
  const [inModifica, setInModifica] = useState(false)
  const [valore, setValore] = useState(impostazione.valore)
  const [salvando, setSalvando] = useState(false)

  const handleSave = async () => {
    setSalvando(true)
    try {
      await onSave(impostazione.id, valore)
      setInModifica(false)
    } finally {
      setSalvando(false)
    }
  }

  const handleCancel = () => {
    setValore(impostazione.valore)
    setInModifica(false)
  }

  return (
    <tr className="border-b border-border last:border-b-0 hover:bg-surface-alt/60">
      <td className="px-4 py-3 align-middle">
        <p className="text-sm font-medium text-ink">{impostazione.chiave}</p>
        <p className="text-xs text-ink-muted">{impostazione.descrizione}</p>
      </td>
      <td className="px-4 py-3 align-middle">
        {inModifica ? (
          <div className="flex items-center gap-2">
            <Input
              value={valore}
              onChange={(e) => setValore(e.target.value)}
              className="h-8 w-24 font-mono text-sm"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSave()
                if (e.key === 'Escape') handleCancel()
              }}
            />
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              aria-label="Salva"
              onClick={handleSave}
              disabled={salvando}
            >
              <Check className="h-3.5 w-3.5 text-success" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              aria-label="Annulla"
              onClick={handleCancel}
            >
              <X className="h-3.5 w-3.5 text-danger" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm text-ink">{impostazione.valore}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100"
              aria-label={`Modifica ${impostazione.chiave}`}
              onClick={() => setInModifica(true)}
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </td>
    </tr>
  )
}

export function ImpostazioniPage() {
  const { data, isLoading } = useImpostazioni()
  const aggiornaMutation = useAggiornaImpostazione()
  const { showToast } = useToast()

  const handleSave = async (id: string, valore: string) => {
    try {
      await aggiornaMutation.mutateAsync({ id, valore })
      showToast('Impostazione salvata.')
    } catch (error) {
      const messaggio =
        error instanceof ApiError ? 'Valore non valido: controlla il formato.' : 'Errore imprevisto.'
      showToast(messaggio, 'error')
      throw error // rilancia per far sapere a RigaImpostazione di restare in modalità edit
    }
  }

  return (
    <div>
      <PageHeader
        title="Impostazioni"
        description="Parametri di configurazione del salone. Clicca su un valore per modificarlo."
      />

      <div className="w-full overflow-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="bg-surface-alt">
            <tr>
              <th className="h-10 px-4 text-left align-middle text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Parametro
              </th>
              <th className="h-10 px-4 text-left align-middle text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Valore
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading ? (
              <tr>
                <td colSpan={2} className="px-4 py-10 text-center text-sm text-ink-muted">
                  Caricamento…
                </td>
              </tr>
            ) : (
              data?.results.map((impostazione) => (
                <RigaImpostazione
                  key={impostazione.id}
                  impostazione={impostazione}
                  onSave={handleSave}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
