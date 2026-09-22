import { apiFetch, creaClientRisorsa } from '@/lib/api'

import type { Servizio, ServizioInput } from './types'

const baseClient = creaClientRisorsa<Servizio, ServizioInput>('/servizi/')

function serializzaPayload(dati: Partial<ServizioInput>): FormData | string {
  if (dati.foto instanceof File) {
    const fd = new FormData()
    for (const [k, v] of Object.entries(dati)) {
      if (v !== undefined && v !== null) {
        if (k === 'foto' && v instanceof File) {
          fd.append('foto', v)
        } else {
          fd.append(k, String(v))
        }
      }
    }
    return fd
  }
  return JSON.stringify(dati)
}

export const servizioApi = {
  ...baseClient,
  crea: (dati: ServizioInput) => {
    const body = serializzaPayload(dati)
    return apiFetch<Servizio>('/servizi/', { method: 'POST', body })
  },
  aggiorna: (id: string, dati: Partial<ServizioInput>) => {
    const body = serializzaPayload(dati)
    return apiFetch<Servizio>(`/servizi/${id}/`, { method: 'PATCH', body })
  },
}
