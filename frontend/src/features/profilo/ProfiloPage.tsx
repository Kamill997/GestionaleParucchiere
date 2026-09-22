import { useState } from 'react'
import { KeyRound, User as UserIcon } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PageHeader } from '@/components/ui/page-header'
import { useToast } from '@/components/ui/toast'
import { useAggiornaProfilo, useCambiaPassword, useCurrentUser } from '@/features/auth/hooks'
import { formattaErroreApi } from '@/lib/api'

import { SessioniCard } from './SessioniCard'

export function ProfiloPage() {
  const { data: user } = useCurrentUser()
  const aggiornaProfiloMutation = useAggiornaProfilo()
  const cambiaPasswordMutation = useCambiaPassword()
  const { showToast } = useToast()

  // Form dati personali
  const [nome, setNome] = useState(user?.nome ?? '')
  const [cognome, setCognome] = useState(user?.cognome ?? '')
  const [telefono, setTelefono] = useState(user?.telefono ?? '')

  // Form cambio password
  const [vecchiaPassword, setVecchiaPassword] = useState('')
  const [nuovaPassword, setNuovaPassword] = useState('')
  const [confermaPassword, setConfermaPassword] = useState('')

  const handleSalvaDati = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await aggiornaProfiloMutation.mutateAsync({
        nome: nome.trim(),
        cognome: cognome.trim(),
        telefono: telefono.trim(),
      })
      showToast('Profilo aggiornato con successo!')
    } catch (err) {
      showToast(formattaErroreApi(err, 'Errore durante l\'aggiornamento del profilo.'), 'error')
    }
  }

  const handleCambiaPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (nuovaPassword !== confermaPassword) {
      showToast('La nuova password e la conferma non coincidono.', 'error')
      return
    }
    if (nuovaPassword.length < 8) {
      showToast('La nuova password deve contenere almeno 8 caratteri.', 'error')
      return
    }

    try {
      await cambiaPasswordMutation.mutateAsync({
        vecchia_password: vecchiaPassword,
        nuova_password: nuovaPassword,
      })
      showToast('Password aggiornata con successo!')
      setVecchiaPassword('')
      setNuovaPassword('')
      setConfermaPassword('')
    } catch (err) {
      showToast(formattaErroreApi(err, 'Errore durante il cambio password.'), 'error')
    }
  }

  return (
    <div className="max-w-4xl space-y-8">
      <PageHeader
        title="Il mio Profilo"
        description="Gestisci i tuoi dati anagrafici e la sicurezza dell'account."
      />

      <div className="grid gap-8 md:grid-cols-2">
        {/* Card Dati Anagrafici */}
        <div className="rounded-lg border border-border bg-surface p-6 shadow-sm">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <UserIcon className="h-5 w-5 text-primary" />
            <h2 className="font-display text-lg font-semibold text-ink">Dati Personali</h2>
          </div>

          <form onSubmit={handleSalvaDati} className="mt-4 space-y-4">
            <div>
              <Label htmlFor="email">Email (non modificabile)</Label>
              <Input id="email" value={user?.email ?? ''} disabled className="bg-surface-alt" />
            </div>

            <div>
              <Label>Ruolo assegnato</Label>
              <div className="mt-1 flex flex-wrap gap-1">
                {user?.ruoli.map((r) => (
                  <Badge key={r} variant="neutral">
                    {r}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <Label htmlFor="nome">Nome</Label>
              <Input
                id="nome"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                placeholder="Il tuo nome"
              />
            </div>

            <div>
              <Label htmlFor="cognome">Cognome</Label>
              <Input
                id="cognome"
                value={cognome}
                onChange={(e) => setCognome(e.target.value)}
                placeholder="Il tuo cognome"
              />
            </div>

            <div>
              <Label htmlFor="telefono">Telefono</Label>
              <Input
                id="telefono"
                type="tel"
                value={telefono}
                onChange={(e) => setTelefono(e.target.value)}
                placeholder="Es. 333 1234567"
              />
            </div>

            <Button type="submit" disabled={aggiornaProfiloMutation.isPending} className="w-full">
              {aggiornaProfiloMutation.isPending ? 'Salvataggio…' : 'Salva modifiche'}
            </Button>
          </form>
        </div>

        {/* Card Sicurezza & Password */}
        <div className="rounded-lg border border-border bg-surface p-6 shadow-sm">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <KeyRound className="h-5 w-5 text-primary" />
            <h2 className="font-display text-lg font-semibold text-ink">Sicurezza Account</h2>
          </div>

          <form onSubmit={handleCambiaPassword} className="mt-4 space-y-4">
            <div>
              <Label htmlFor="vecchia_password">Password Attuale</Label>
              <Input
                id="vecchia_password"
                type="password"
                value={vecchiaPassword}
                onChange={(e) => setVecchiaPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            <div>
              <Label htmlFor="nuova_password">Nuova Password</Label>
              <Input
                id="nuova_password"
                type="password"
                value={nuovaPassword}
                onChange={(e) => setNuovaPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
              <p className="mt-1 text-xs text-ink-muted">Minimo 8 caratteri.</p>
            </div>

            <div>
              <Label htmlFor="conferma_password">Conferma Nuova Password</Label>
              <Input
                id="conferma_password"
                type="password"
                value={confermaPassword}
                onChange={(e) => setConfermaPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
            </div>

            <Button
              type="submit"
              variant="secondary"
              disabled={cambiaPasswordMutation.isPending}
              className="w-full"
            >
              {cambiaPasswordMutation.isPending ? 'Aggiornamento…' : 'Aggiorna password'}
            </Button>
          </form>
        </div>
      </div>

      <SessioniCard />
    </div>
  )
}
