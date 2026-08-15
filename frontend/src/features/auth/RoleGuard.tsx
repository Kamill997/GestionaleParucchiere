import type { ReactNode } from 'react'

import { useCurrentUser } from './hooks'

/**
 * Guard lato frontend: nasconde `children` se l'utente non ha uno dei
 * ruoli richiesti. Non sostituisce i controlli lato backend (unico posto
 * dove la sicurezza e' davvero applicata) - serve solo a non mostrare
 * azioni che comunque il server rifiuterebbe.
 */
export function RoleGuard({ roles, children }: { roles: string[]; children: ReactNode }) {
  const { data: user } = useCurrentUser()
  if (!user) return null
  const autorizzato = user.ruoli.some((ruolo) => roles.includes(ruolo))
  return autorizzato ? <>{children}</> : null
}
