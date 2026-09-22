import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { formattaErroreApi } from '@/lib/api'

import { ensureCsrfCookie } from './api'
import { useCurrentUser, useRegister } from './hooks'

const registerSchema = z
  .object({
    nome: z.string().min(1, 'Il nome è obbligatorio'),
    cognome: z.string().optional(),
    telefono: z.string().optional(),
    email: z.string().min(1, "L'email è obbligatoria").email('Email non valida'),
    password: z.string().min(8, 'La password deve avere almeno 8 caratteri'),
    conferma_password: z.string().min(1, 'La conferma password è obbligatoria'),
  })
  .refine((data) => data.password === data.conferma_password, {
    message: 'Le password non coincidono',
    path: ['conferma_password'],
  })

type RegisterFormValues = z.infer<typeof registerSchema>

export function RegisterPage() {
  const { data: user } = useCurrentUser()
  const navigate = useNavigate()
  const registerMutation = useRegister()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  })

  useEffect(() => {
    ensureCsrfCookie().catch(() => {})
  }, [])

  if (user) {
    return <Navigate to="/" replace />
  }

  const onSubmit = handleSubmit(async (values) => {
    try {
      await registerMutation.mutateAsync({
        email: values.email,
        password: values.password,
        nome: values.nome,
        cognome: values.cognome || undefined,
        telefono: values.telefono || undefined,
      })
      navigate('/', { replace: true })
    } catch {
      // Errore gestito e visualizzato tramite registerMutation.error
    }
  })

  const apiErrorMessage = registerMutation.error
    ? formattaErroreApi(registerMutation.error)
    : null

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4 py-8">
      <div className="w-full max-w-md rounded-lg border border-border bg-surface p-8 shadow-sm">
        <h1 className="font-display text-2xl font-semibold text-ink">Crea il tuo account</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Registrati per prenotare e gestire i tuoi appuntamenti al salone.
        </p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="nome">Nome *</Label>
              <Input
                id="nome"
                type="text"
                autoComplete="given-name"
                invalid={!!errors.nome}
                {...register('nome')}
              />
              {errors.nome && <p className="mt-1 text-sm text-danger">{errors.nome.message}</p>}
            </div>

            <div>
              <Label htmlFor="cognome">Cognome</Label>
              <Input
                id="cognome"
                type="text"
                autoComplete="family-name"
                invalid={!!errors.cognome}
                {...register('cognome')}
              />
              {errors.cognome && (
                <p className="mt-1 text-sm text-danger">{errors.cognome.message}</p>
              )}
            </div>
          </div>

          <div>
            <Label htmlFor="telefono">Telefono</Label>
            <Input
              id="telefono"
              type="tel"
              autoComplete="tel"
              placeholder="Es. 333 1234567"
              invalid={!!errors.telefono}
              {...register('telefono')}
            />
            {errors.telefono && (
              <p className="mt-1 text-sm text-danger">{errors.telefono.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="email">Email *</Label>
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
            <Label htmlFor="password">Password *</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              invalid={!!errors.password}
              {...register('password')}
            />
            {errors.password && (
              <p className="mt-1 text-sm text-danger">{errors.password.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="conferma_password">Conferma Password *</Label>
            <Input
              id="conferma_password"
              type="password"
              autoComplete="new-password"
              invalid={!!errors.conferma_password}
              {...register('conferma_password')}
            />
            {errors.conferma_password && (
              <p className="mt-1 text-sm text-danger">{errors.conferma_password.message}</p>
            )}
          </div>

          {apiErrorMessage && (
            <p className="text-sm text-danger" role="alert">
              {apiErrorMessage}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={registerMutation.isPending}>
            {registerMutation.isPending ? 'Creazione account in corso…' : 'Registrati'}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-ink-muted">Hai già un account? </span>
          <Link to="/login" className="font-medium text-primary hover:underline">
            Accedi
          </Link>
        </div>

        <p className="mt-6 text-center text-xs text-ink-muted">
          Registrandoti accetti i{' '}
          <Link to="/termini" className="underline hover:text-ink">
            Termini
          </Link>{' '}
          e la{' '}
          <Link to="/privacy" className="underline hover:text-ink">
            Privacy Policy
          </Link>
          .
        </p>
      </div>
    </div>
  )
}
