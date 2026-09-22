import { apiFetch, creaClientRisorsa } from '@/lib/api'

import type {
  Prenotazione,
  PrenotazioneInput,
  RichiestaListaAttesa,
  RichiestaListaAttesaInput,
  SlotDisponibile,
  StatoPresenza,
} from './types'

export const prenotazioneApi = creaClientRisorsa<Prenotazione, PrenotazioneInput>('/prenotazioni/')
export const listaAttesaApi = creaClientRisorsa<RichiestaListaAttesa, RichiestaListaAttesaInput>('/lista-attesa/')

export function fetchSlotDisponibili(
  operatore: string,
  servizio: string,
  data: string,
  serviziAggiuntivi?: string[]
) {
  const params = new URLSearchParams({ operatore, servizio, data })
  if (serviziAggiuntivi && serviziAggiuntivi.length > 0) {
    params.set('servizi_aggiuntivi', serviziAggiuntivi.join(','))
  }
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

export function annullaRichiestaListaAttesa(id: string) {
  return apiFetch<RichiestaListaAttesa>(`/lista-attesa/${id}/annulla/`, { method: 'POST' })
}
