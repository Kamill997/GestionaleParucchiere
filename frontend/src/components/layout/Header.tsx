import { LogOut } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useCurrentUser, useLogout } from '@/features/auth/hooks'

export function Header() {
  const { data: user } = useCurrentUser()
  const logoutMutation = useLogout()

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-surface px-6">
      <div />
      {user && (
        <div className="flex items-center gap-4">
          <div className="text-right leading-tight">
            <p className="text-sm font-medium text-ink">
              {[user.nome, user.cognome].filter(Boolean).join(' ') || user.email}
            </p>
            <p className="text-xs text-ink-muted">{user.ruoli.join(', ') || 'Nessun ruolo'}</p>
          </div>
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
