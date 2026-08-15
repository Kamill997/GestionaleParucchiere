import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError } from '@/lib/api'

import { ensureCsrfCookie } from './api'
import { useCurrentUser, useLogin } from './hooks'

const loginSchema = z.object({
  email: z.string().min(1, "L'email è obbligatoria").email('Email non valida'),
  password: z.string().min(1, 'La password è obbligatoria'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export function LoginPage() {
  const { data: user } = useCurrentUser()
  const navigate = useNavigate()
  const location = useLocation()
  const loginMutation = useLogin()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) })

  // Il cookie csrftoken serve fin dal primo render (es. se l'utente arriva
  // gia' con un cookie scaduto e la pagina fa altre chiamate mutanti).
  useEffect(() => {
    ensureCsrfCookie().catch(() => {
      // Se il cookie CSRF non si imposta (backend irraggiungibile, rete...),
      // il tentativo di login fallira' comunque in modo esplicito al submit:
      // qui non c'e' nulla di utile da mostrare all'utente in anticipo.
    })
  }, [])

  if (user) {
    const redirectTo = (location.state as { from?: Location })?.from?.pathname ?? '/'
    return <Navigate to={redirectTo} replace />
  }

  const onSubmit = handleSubmit(async (values) => {
    try {
      await loginMutation.mutateAsync(values)
      navigate('/', { replace: true })
    } catch {
      // l'errore e' gia' esposto tramite loginMutation.error qui sotto
    }
  })

  const credentialsAreInvalid =
    loginMutation.error instanceof ApiError && loginMutation.error.status === 401

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm rounded-lg border border-border bg-surface p-8 shadow-sm">
        <h1 className="font-display text-2xl font-semibold text-ink">Gestionale Salone</h1>
        <p className="mt-1 text-sm text-ink-muted">Accedi con le tue credenziali.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              invalid={!!errors.email}
              {...register('email')}
            />
            {errors.email && <p className="mt-1 text-sm text-danger">{errors.email.message}</p>}
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              invalid={!!errors.password}
              {...register('password')}
            />
            {errors.password && (
              <p className="mt-1 text-sm text-danger">{errors.password.message}</p>
            )}
          </div>

          {credentialsAreInvalid && (
            <p className="text-sm text-danger" role="alert">
              Email o password non corrette.
            </p>
          )}

          <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? 'Accesso in corso…' : 'Accedi'}
          </Button>
        </form>
      </div>
    </div>
  )
}
