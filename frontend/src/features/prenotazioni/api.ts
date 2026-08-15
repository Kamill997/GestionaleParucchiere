import { apiFetch, creaClientRisorsa } from '@/lib/api'

import type { Prenotazione, PrenotazioneInput, SlotDisponibile, StatoPresenza } from './types'

export const prenotazioneApi = creaClientRisorsa<Prenotazione, PrenotazioneInput>('/prenotazioni/')

export function fetchSlotDisponibili(operatore: string, servizio: string, data: string) {
  const params = new URLSearchParams({ operatore, servizio, data })
  return apiFetch<SlotDisponibile[]>(`/slot-disponibili/?${params.toString()}`)
}

export function cancellaPrenotazione(id: string) {
  return apiFetch<Prenotazione>(`/prenotazioni/${id}/cancella/`, { method: 'POST' })
}

export function segnaPresenza(id: string, stato_presenza: StatoPresenza) {
  return apiFetch<Prenotazione>(`/prenotazioni/${id}/segna-presenza/`, {
    method: 'POST',
    body: JSON.stringify({ stato_presenza }),
  })
}
