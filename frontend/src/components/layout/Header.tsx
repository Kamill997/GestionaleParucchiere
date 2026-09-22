import { LogOut } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { InstallButton } from '@/components/pwa/InstallButton'
import { useCurrentUser, useLogout } from '@/features/auth/hooks'
import { NotificationBell } from '@/features/notifiche/NotificationBell'

export function Header() {
  const { data: user } = useCurrentUser()
  const logoutMutation = useLogout()

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-surface px-6">
      <div />
      {user && (
        <div className="flex items-center gap-4">
          <InstallButton />
          <NotificationBell />
          <Link
            to="/profilo"
            className="text-right leading-tight transition-colors hover:text-primary"
            title="Visualizza il tuo profilo"
          >
            <p className="text-sm font-medium text-ink">
              {[user.nome, user.cognome].filter(Boolean).join(' ') || user.email}
            </p>
            <p className="text-xs text-ink-muted">{user.ruoli.join(', ') || 'Nessun ruolo'}</p>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Esci"
            onClick={() => logoutMutation.mutate()}
            disabled={logoutMutation.isPending}
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      )}
    </header>
  )
}
