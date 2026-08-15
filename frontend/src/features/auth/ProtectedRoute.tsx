import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useCurrentUser } from './hooks'

export function ProtectedRoute() {
  const { data: user, isPending } = useCurrentUser()
  const location = useLocation()

  if (isPending) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-ink-muted">
        Caricamento…
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}
