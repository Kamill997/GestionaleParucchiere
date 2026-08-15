import { apiFetch, creaClientRisorsa } from '@/lib/api'

import type { Cliente, ClienteInput } from './types'

export const clienteApi = creaClientRisorsa<Cliente, ClienteInput>('/clienti/')

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

// docs/07-import-export-dati.md: template/export sono download GET, quindi
// bastano URL diretti (navigazione, non fetch) - il cookie JWT httpOnly
// viaggia comunque su una navigazione top-level con SameSite=Lax, e le
// richieste GET non richiedono l'header X-CSRFToken (vedi
// backend/common/authentication.py, CSRFCheck salta i metodi "safe").
export function urlTemplateImportClienti() {
  return `${API_URL}/clienti/template-import/`
}

export function urlEsportaClienti(ricerca?: string) {
  const params = new URLSearchParams()
  if (ricerca) params.set('search', ricerca)
  const query = params.toString()
  return `${API_URL}/clienti/esporta/${query ? `?${query}` : ''}`
}

export interface RigaErroreImportazione {
  riga: number
  messaggio: string
}

export interface RigaDuplicataImportazione {
  riga: number
  email: string
}

export interface ReportImportazioneClienti {
  creati: number
  aggiornati: number
  errori: RigaErroreImportazione[]
  duplicati_interni: RigaDuplicataImportazione[]
}

// POST multipart: usa apiFetch (non i metodi generici di creaClientRisorsa,
// che assumono sempre JSON) cosi' l'header X-CSRFToken resta automatico.
export function importaClienti(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return apiFetch<ReportImportazioneClienti>('/clienti/importa/', {
    method: 'POST',
    body: formData,
  })
}
