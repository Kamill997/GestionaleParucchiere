import { apiFetch, creaClientRisorsa } from '@/lib/api'

import type { Notifica } from './types'

export const notificaApi = creaClientRisorsa<Notifica>('/notifiche/')

export function fetchNonLetteCount() {
  return apiFetch<{ conteggio: number }>('/notifiche/non-lette-count/')
}

export function segnaLetta(id: string) {
  return apiFetch<Notifica>(`/notifiche/${id}/segna-letta/`, { method: 'POST' })
}

export function segnaTutteLette() {
  return apiFetch<{ aggiornate: number }>('/notifiche/segna-tutte-lette/', { method: 'POST' })
}
