import { apiFetch } from '@/lib/api'
import type { RisultatoPaginato } from '@/lib/api'

import type { Impostazione } from './types'

export function fetchImpostazioni() {
  return apiFetch<RisultatoPaginato<Impostazione>>('/impostazioni/')
}

export function aggiornaImpostazione(id: string, valore: string) {
  return apiFetch<Impostazione>(`/impostazioni/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify({ valore }),
  })
}
