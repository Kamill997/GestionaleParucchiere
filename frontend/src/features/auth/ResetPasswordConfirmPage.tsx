import { useState } from 'react'
import { CheckCircle2, KeyRound } from 'lucide-react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/toast'
import { useConfermaResetPassword } from '@/features/auth/hooks'
import { formattaErroreApi } from '@/lib/api'

export function ResetPasswordConfirmPage() {
  const [searchParams] = useSearchParams()
  const uid = searchParams.get('uid') ?? ''
  const token = searchParams.get('token') ?? ''

  const [nuovaPassword, setNuovaPassword] = useState('')
  const [confermaPassword, setConfermaPassword] = useState('')
  const [completato, setCompletato] = useState(false)

  const confermaMutation = useConfermaResetPassword()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!uid || !token) {
      showToast('Link di ripristino non valido o incompleto.', 'error')
      return
    }

    if (nuovaPassword !== confermaPassword) {
      showToast('La nuova password e la conferma non coincidono.', 'error')
      return
    }

    if (nuovaPassword.length < 8) {
      showToast('La password deve contenere almeno 8 caratteri.', 'error')
      return
    }

    try {
      await confermaMutation.mutateAsync({
        uid,
        token,
        nuova_password: nuovaPassword,
      })
      setCompletato(true)
      showToast('Password reimpostata con successo!')
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      showToast(formattaErroreApi(err, 'Il link non è più valido o è scaduto.'), 'error')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-md rounded-lg border border-border bg-surface p-8 shadow-sm">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
          <KeyRound className="h-6 w-6" />
        </div>

        <h1 className="mt-4 font-display text-2xl font-semibold text-ink">
          Crea una nuova password
        </h1>
        <p className="mt-1 text-sm text-ink-muted">
          Inserisci la tua nuova password per accedere al tuo account.
        </p>

        {completato ? (
          <div className="mt-6 rounded-lg bg-surface-alt p-4 text-center">
            <CheckCircle2 className="mx-auto h-8 w-8 text-success" />
            <p className="mt-2 text-sm font-medium text-ink">Password aggiornata!</p>
            <p className="mt-1 text-xs text-ink-muted">Verrai reindirizzato al login tra un istante…</p>
            <Button asChild variant="primary" className="mt-4 w-full">
              <Link to="/login">Accedi subito</Link>
            </Button>
          </div>
        ) : !uid || !token ? (
          <div className="mt-6 rounded-lg border border-danger/20 bg-danger/5 p-4 text-center">
            <p className="text-sm font-medium text-danger">Link di ripristino non valido</p>
            <p className="mt-1 text-xs text-ink-muted">
              Il link utilizzato sembra incompleto o errato. Richiedi un nuovo link di recupero.
            </p>
            <Button asChild variant="secondary" className="mt-4 w-full">
              <Link to="/password-dimenticata">Richiedi nuovo link</Link>
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <Label htmlFor="nuova_password">Nuova password</Label>
              <Input
                id="nuova_password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={nuovaPassword}
                onChange={(e) => setNuovaPassword(e.target.value)}
              />
              <p className="mt-1 text-xs text-ink-muted">Minimo 8 caratteri.</p>
            </div>

            <div>
              <Label htmlFor="conferma_password">Conferma nuova password</Label>
              <Input
                id="conferma_password"
                type="password"
                required
                autoComplete="new-password"
                value={confermaPassword}
                onChange={(e) => setConfermaPassword(e.target.value)}
              />
            </div>

            <Button type="submit" className="w-full" disabled={confermaMutation.isPending}>
              {confermaMutation.isPending ? 'Reimpostazione in corso…' : 'Reimposta password'}
            </Button>
          </form>
        )}
      </div>
    </div>
  )
}
