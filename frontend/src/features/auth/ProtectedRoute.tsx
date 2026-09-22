import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useCurrentUser } from './hooks'

/**
 * Protegge le rotte richiedendo autenticazione e, opzionalmente, uno o piu'
 * ruoli specifici. Se l'utente non e' autenticato, reindirizza al login.
 * Se e' autenticato ma senza i ruoli richiesti, reindirizza alla dashboard.
 *
 * Quando usato come guard annidato (con `roles`), l'utente e' gia' stato
 * verificato dal ProtectedRoute esterno: in quel caso il dato e' gia' in
 * cache e `isPending` e' `false` al primo render (staleTime 5 min).
 */
export function ProtectedRoute({ roles }: { roles?: string[] }) {
  const { data: user, isPending } = useCurrentUser()
  const location = useLocation()

  // Fase di caricamento: mostra uno spinner solo se non abbiamo ancora
  // dati. Quando usato come guard annidato il dato e' gia' in cache.
  if (isPending && !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-ink-muted">
        Caricamento…
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Controllo ruoli: se specificati, l'utente deve averne almeno uno.
  // Altrimenti reindirizza alla dashboard (non un 403, perche' la rotta
  // semplicemente non e' destinata a questo ruolo).
  if (roles && !roles.some((r) => user.ruoli.includes(r))) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
