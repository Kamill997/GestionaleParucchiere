import { useState } from 'react'
import { ArrowLeft, CheckCircle2, Mail } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/toast'
import { useRichiediResetPassword } from '@/features/auth/hooks'
import { formattaErroreApi } from '@/lib/api'

export function RichiediResetPasswordPage() {
  const [email, setEmail] = useState('')
  const [inviata, setInviata] = useState(false)
  const richiediMutation = useRichiediResetPassword()
  const { showToast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return

    try {
      await richiediMutation.mutateAsync(email.trim())
      setInviata(true)
    } catch (err) {
      showToast(formattaErroreApi(err, 'Impossibile inviare la richiesta.'), 'error')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-md rounded-lg border border-border bg-surface p-8 shadow-sm">
        <div className="mb-6">
          <Button asChild variant="ghost" size="sm">
            <Link to="/login">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Torna al login
            </Link>
          </Button>
        </div>

        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Mail className="h-6 w-6" />
        </div>

        <h1 className="mt-4 font-display text-2xl font-semibold text-ink">
          Hai dimenticato la password?
        </h1>
        <p className="mt-1 text-sm text-ink-muted">
          Inserisci la tua email e ti invieremo un link sicuro per reimpostarla.
        </p>

        {inviata ? (
          <div className="mt-6 rounded-lg bg-surface-alt p-4 text-center">
            <CheckCircle2 className="mx-auto h-8 w-8 text-success" />
            <p className="mt-2 text-sm font-medium text-ink">Controlla la tua casella di posta</p>
            <p className="mt-1 text-xs text-ink-muted">
              Se l'indirizzo <strong>{email}</strong> è registrato, riceverai a breve un'email con le istruzioni.
            </p>
            <Button asChild variant="secondary" className="mt-4 w-full">
              <Link to="/login">Torna al Login</Link>
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <Label htmlFor="email">La tua email</Label>
              <Input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nome@esempio.it"
              />
            </div>

            <Button type="submit" className="w-full" disabled={richiediMutation.isPending}>
              {richiediMutation.isPending ? 'Invio in corso…' : 'Invia link di ripristino'}
            </Button>
          </form>
        )}
      </div>
    </div>
  )
}
