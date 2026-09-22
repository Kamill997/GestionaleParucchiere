import { apiFetch, creaClientRisorsa, type RisultatoPaginato } from '@/lib/api'

import type {
  Disponibilita,
  EccezioneDisponibilita,
  EccezioneDisponibilitaInput,
  GiornoTurnoInput,
  Operatore,
  OperatoreInput,
} from './types'

export const operatoreApi = creaClientRisorsa<Operatore, OperatoreInput>('/operatori/')

export function fetchDisponibilitaOperatore(operatoreId: string) {
  return apiFetch<RisultatoPaginato<Disponibilita>>(`/disponibilita/?operatore=${operatoreId}`)
}

export function salvaTurniSettimana(operatoreId: string, giorni: GiornoTurnoInput[]) {
  return apiFetch<Disponibilita[]>('/disponibilita/imposta-settimana/', {
    method: 'POST',
    body: JSON.stringify({ operatore: operatoreId, giorni }),
  })
}

export function fetchEccezioni(params?: Record<string, string | undefined>) {
  if (!params) return apiFetch<RisultatoPaginato<EccezioneDisponibilita>>('/eccezioni-disponibilita/')
  const cleanParams: Record<string, string> = {}
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) cleanParams[k] = v
  }
  const qry = new URLSearchParams(cleanParams).toString()
  return apiFetch<RisultatoPaginato<EccezioneDisponibilita>>(`/eccezioni-disponibilita/${qry ? `?${qry}` : ''}`)
}

export function creaEccezione(dati: EccezioneDisponibilitaInput) {
  return apiFetch<EccezioneDisponibilita>('/eccezioni-disponibilita/', {
    method: 'POST',
    body: JSON.stringify(dati),
  })
}

export function eliminaEccezione(id: string) {
  return apiFetch<void>(`/eccezioni-disponibilita/${id}/`, {
    method: 'DELETE',
  })
}

