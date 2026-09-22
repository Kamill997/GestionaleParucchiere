import { useState } from 'react'
import { Clock, Globe, Laptop, LogOut, ShieldCheck, Smartphone, Tablet } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { useToast } from '@/components/ui/toast'
import {
  useRevocaAltreSessioni,
  useRevocaSessione,
  useRevocaTutteSessioni,
  useSessioniUtente,
} from '@/features/auth/hooks'
import { formattaErroreApi } from '@/lib/api'

function getDeviceIcon(dispositivo: string) {
  const d = (dispositivo || '').toLowerCase()
  if (d.includes('iphone') || d.includes('android') || d.includes('mobile')) {
    return <Smartphone className="h-5 w-5 text-primary" />
  }
  if (d.includes('ipad') || d.includes('tablet')) {
    return <Tablet className="h-5 w-5 text-primary" />
  }
  return <Laptop className="h-5 w-5 text-primary" />
}

export function SessioniCard() {
  const { data: sessioni, isLoading, isError } = useSessioniUtente()
  const revocaSessioneMutation = useRevocaSessione()
  const revocaAltreMutation = useRevocaAltreSessioni()
  const revocaTutteMutation = useRevocaTutteSessioni()
  const { showToast } = useToast()

  const [sessioneDaRevocare, setSessioneDaRevocare] = useState<string | null>(null)
  const [altreModalOpen, setAltreModalOpen] = useState(false)
  const [tutteModalOpen, setTutteModalOpen] = useState(false)

  const altreSessioni = sessioni?.filter((s) => !s.e_corrente) ?? []

  const handleRevocaSingola = async () => {
    if (!sessioneDaRevocare) return
    try {
      await revocaSessioneMutation.mutateAsync(sessioneDaRevocare)
      showToast('Dispositivo disconnesso con successo.')
      setSessioneDaRevocare(null)
    } catch (err) {
      showToast(formattaErroreApi(err, 'Impossibile disconnettere il dispositivo.'), 'error')
    }
  }

  const handleRevocaAltre = async () => {
    try {
      await revocaAltreMutation.mutateAsync()
      showToast('Tutti gli altri dispositivi sono stati disconnessi.')
      setAltreModalOpen(false)
    } catch (err) {
      showToast(formattaErroreApi(err, 'Impossibile disconnettere gli altri dispositivi.'), 'error')
    }
  }

  const handleRevocaTutte = async () => {
    try {
      await revocaTutteMutation.mutateAsync()
      showToast('Tutte le sessioni sono state revocate. Effettua nuovamente il login.')
      setTutteModalOpen(false)
    } catch (err) {
      showToast(formattaErroreApi(err, 'Impossibile revocare tutte le sessioni.'), 'error')
    }
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-6 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-primary" />
          <div>
            <h2 className="font-display text-lg font-semibold text-ink">
              Dispositivi e Sessioni Attive
            </h2>
            <p className="text-xs text-ink-muted">
              Elenco dei browser e dispositivi attualmente collegati al tuo account.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {altreSessioni.length > 0 && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setAltreModalOpen(true)}
              disabled={revocaAltreMutation.isPending}
            >
              Disconnetti altri dispositivi ({altreSessioni.length})
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="text-danger hover:bg-danger-soft hover:text-danger"
            onClick={() => setTutteModalOpen(true)}
            disabled={revocaTutteMutation.isPending}
          >
            <LogOut className="h-4 w-4 mr-1" />
            Disconnetti ovunque
          </Button>
        </div>
      </div>

      <div className="mt-4">
        {isLoading && (
          <p className="text-sm text-ink-muted py-4 text-center">Caricamento sessioni in corso…</p>
        )}

        {isError && (
          <p className="text-sm text-danger py-4 text-center">
            Impossibile caricare l'elenco delle sessioni attive.
          </p>
        )}

        {!isLoading && !isError && (!sessioni || sessioni.length === 0) && (
          <p className="text-sm text-ink-muted py-4 text-center">Nessuna sessione attiva trovata.</p>
        )}

        {sessioni && sessioni.length > 0 && (
          <div className="divide-y divide-border">
            {sessioni.map((s) => (
              <div
                key={s.id}
                className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-4 first:pt-2 last:pb-2 ${
                  s.e_corrente ? 'bg-primary-soft/20 -mx-3 px-3 rounded-md' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-1 rounded-full bg-surface-alt p-2">
                    {getDeviceIcon(s.dispositivo)}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-ink">{s.dispositivo}</span>
                      {s.e_corrente ? (
                        <Badge variant="success">Dispositivo attuale</Badge>
                      ) : (
                        <Badge variant="neutral">Attiva</Badge>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-muted">
                      {s.ip_address && (
                        <span className="flex items-center gap-1">
                          <Globe className="h-3.5 w-3.5" />
                          IP: {s.ip_address}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        Ultimo accesso:{' '}
                        {new Date(s.ultimo_accesso).toLocaleString('it-IT', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                  </div>
                </div>

                {!s.e_corrente && (
                  <div className="sm:self-center">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setSessioneDaRevocare(s.id)}
                      disabled={revocaSessioneMutation.isPending}
                    >
                      Disconnetti
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modale conferma revoca singola sessione */}
      <ConfirmDialog
        open={Boolean(sessioneDaRevocare)}
        onOpenChange={(open) => !open && setSessioneDaRevocare(null)}
        title="Disconnetti dispositivo"
        description="Sei sicuro di voler terminare questa sessione? L'utente sul dispositivo dovrà effettuare nuovamente il login."
        confirmLabel="Disconnetti"
        destructive
        isLoading={revocaSessioneMutation.isPending}
        onConfirm={handleRevocaSingola}
      />

      {/* Modale conferma revoca altre sessioni */}
      <ConfirmDialog
        open={altreModalOpen}
        onOpenChange={setAltreModalOpen}
        title="Disconnetti tutti gli altri dispositivi"
        description={`Verranno revocate ${altreSessioni.length} altre sessioni attive. Solo questo dispositivo rimarrà connesso.`}
        confirmLabel="Disconnetti tutti gli altri"
        destructive
        isLoading={revocaAltreMutation.isPending}
        onConfirm={handleRevocaAltre}
      />

      {/* Modale conferma revoca tutte le sessioni (globale) */}
      <ConfirmDialog
        open={tutteModalOpen}
        onOpenChange={setTutteModalOpen}
        title="Disconnetti ovunque (Logout globale)"
        description="ATTENZIONE: Verranno invalidate tutte le sessioni attive, compresa quella corrente. Verrai reindirizzato alla pagina di login."
        confirmLabel="Disconnetti ovunque"
        destructive
        isLoading={revocaTutteMutation.isPending}
        onConfirm={handleRevocaTutte}
      />
    </div>
  )
}
