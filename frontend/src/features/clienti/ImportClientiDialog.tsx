import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError } from '@/lib/api'

import { urlTemplateImportClienti } from './api'
import { useImportaClienti } from './hooks'
import type { ReportImportazioneClienti } from './api'

/**
 * docs/07-import-export-dati.md, "Flusso di importazione": upload + report
 * finale (righe create/aggiornate/in errore). Scope ridotto dichiarato in
 * stato-avanzamento.md: un solo step (nessuna anteprima/mappatura colonne,
 * il template scaricato ha gia' le colonne fisse attese).
 */
export function ImportClientiDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [report, setReport] = useState<ReportImportazioneClienti | null>(null)
  const importMutation = useImportaClienti()

  const chiudi = () => {
    onOpenChange(false)
    // Reset posticipato: il modale ha un'animazione di chiusura, azzerare
    // subito farebbe "sparire" il report un istante prima che si chiuda.
    setTimeout(() => {
      setFile(null)
      setReport(null)
      importMutation.reset()
    }, 150)
  }

  const handleImporta = async () => {
    if (!file) return
    try {
      const risultato = await importMutation.mutateAsync(file)
      setReport(risultato)
    } catch {
      // errore gia' esposto sotto tramite importMutation.error
    }
  }

  const messaggioErrore =
    importMutation.error instanceof ApiError
      ? (importMutation.error.body as { detail?: string })?.detail ||
        'File non valido: verifica formato e colonne.'
      : null

  return (
    <Dialog open={open} onOpenChange={(o) => !o && chiudi()}>
      <DialogContent
        title="Importa clienti"
        description="File CSV o Excel (max 5MB), colonne: nome, email, telefono, note_preferenze."
      >
        {!report ? (
          <div className="space-y-4">
            <a
              href={urlTemplateImportClienti()}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-primary underline-offset-4 hover:underline"
            >
              Scarica il template CSV
            </a>

            <div>
              <Label htmlFor="file-import-clienti">File</Label>
              <Input
                id="file-import-clienti"
                type="file"
                accept=".csv,.xlsx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </div>

            {messaggioErrore && (
              <p className="text-sm text-danger" role="alert">
                {messaggioErrore}
              </p>
            )}

            <DialogFooter>
              <Button type="button" variant="secondary" onClick={chiudi}>
                Annulla
              </Button>
              <Button
                type="button"
                onClick={handleImporta}
                disabled={!file || importMutation.isPending}
              >
                {importMutation.isPending ? 'Caricamento…' : 'Importa'}
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-md bg-success-soft p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-success">Creati</p>
                <p className="font-display text-xl font-semibold text-success">{report.creati}</p>
              </div>
              <div className="rounded-md bg-primary-soft p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-primary">
                  Aggiornati
                </p>
                <p className="font-display text-xl font-semibold text-primary">
                  {report.aggiornati}
                </p>
              </div>
            </div>

            {report.duplicati_interni.length > 0 && (
              <p className="text-sm text-warning">
                {report.duplicati_interni.length} email ripetute nel file: ha vinto l'ultima riga
                per ciascuna.
              </p>
            )}

            {report.errori.length > 0 && (
              <div>
                <p className="text-sm font-medium text-danger">
                  {report.errori.length} righe scartate:
                </p>
                <ul className="mt-1 max-h-32 space-y-1 overflow-auto text-xs text-ink-muted">
                  {report.errori.map((errore) => (
                    <li key={errore.riga}>
                      Riga {errore.riga}: {errore.messaggio}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.creati === 0 && report.aggiornati === 0 && report.errori.length === 0 && (
              <p className="text-sm text-ink-muted">Il file non conteneva righe da importare.</p>
            )}

            <DialogFooter>
              <Button type="button" onClick={chiudi}>
                Chiudi
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
