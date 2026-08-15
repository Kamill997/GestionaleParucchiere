import type { ComponentType } from 'react'
import {
  CalendarCheck,
  CalendarPlus,
  LayoutDashboard,
  ListChecks,
  Scissors,
  UserCog,
  UserRound,
  Users,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { useCurrentUser } from '@/features/auth/hooks'
import { cn } from '@/lib/utils'

interface NavItem {
  to: string
  label: string
  icon: ComponentType<{ className?: string }>
  /** Se omesso, visibile a chiunque sia autenticato. */
  roles?: string[]
}

// Solo le voci di navigazione che esistono davvero: altre arrivano un
// modulo alla volta insieme alle relative pagine (vedi docs/10-guida-vibe-coding.md).
const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/servizi', label: 'Servizi', icon: Scissors },
  { to: '/prenota', label: 'Prenota', icon: CalendarPlus },
  { to: '/le-mie-prenotazioni', label: 'Le mie prenotazioni', icon: ListChecks },
  {
    to: '/gestione-prenotazioni',
    label: 'Gestione prenotazioni',
    icon: CalendarCheck,
    roles: ['Amministratore', 'Operatore'],
  },
  { to: '/operatori', label: 'Operatori', icon: Users, roles: ['Amministratore'] },
  { to: '/clienti', label: 'Clienti', icon: UserRound, roles: ['Amministratore', 'Operatore'] },
  { to: '/utenti', label: 'Utenti e ruoli', icon: UserCog, roles: ['Amministratore'] },
]

export function Sidebar() {
  const { data: user } = useCurrentUser()
  const voci = NAV_ITEMS.filter(
    (item) => !item.roles || item.roles.some((r) => user?.ruoli.includes(r)),
  )

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-border bg-surface-alt">
      <div className="flex h-16 items-center px-6">
        <span className="font-display text-lg font-semibold text-ink">Salone</span>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {voci.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md border-l-4 border-transparent px-3 py-2 text-sm font-medium text-ink-muted transition-colors',
                'hover:bg-surface hover:text-ink',
                isActive && 'border-primary bg-surface text-primary',
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
