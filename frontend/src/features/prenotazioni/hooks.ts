import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { cancellaPrenotazione, fetchSlotDisponibili, prenotazioneApi, segnaPresenza } from './api'
import type { PrenotazioneInput, StatoPagamento, StatoPresenza } from './types'

const CHIAVE_PRENOTAZIONI = ['prenotazioni'] as const

export function useLeMiePrenotazioni(pagina = 1) {
  return useQuery({
    queryKey: [...CHIAVE_PRENOTAZIONI, pagina],
    queryFn: () => prenotazioneApi.lista(`?page=${pagina}`),
  })
}

/** Vista staff: stesso endpoint di useLeMiePrenotazioni, ma il backend
 * restituisce tutte le prenotazioni (Amministratore) o quelle assegnate
 * (Operatore) invece di scoparle al singolo cliente - vedi
 * apps/prenotazioni/views.py, PrenotazioneViewSet.get_queryset. */
export function useTuttePrenotazioni(pagina = 1, stato?: string) {
  const params = new URLSearchParams({ page: String(pagina), ordering: '-inizio' })
  if (stato) params.set('stato', stato)

  return useQuery({
    queryKey: [...CHIAVE_PRENOTAZIONI, 'tutte', pagina, stato],
    queryFn: () => prenotazioneApi.lista(`?${params.toString()}`),
  })
}

export function useProssimoAppuntamento() {
  return useQuery({
    queryKey: [...CHIAVE_PRENOTAZIONI, 'prossimo'],
    // Non esiste ancora un filtro server-side "inizio >= adesso" (nessuna
    // transizione automatica confermata -> completata col passare del
    // tempo): si prende un campione ordinato e si trova il primo futuro
    // lato client. Con page_size=1 il piu' vicino potrebbe gia' essere
    // passato, dando sempre null anche se ce ne sono di futuri.
    queryFn: () => prenotazioneApi.lista('?stato=confermata&ordering=inizio&page_size=20'),
    select: (dati) => dati.results.find((p) => new Date(p.inizio) > new Date()) ?? null,
  })
}

export function useSlotDisponibili(operatore: string, servizio: string, data: string) {
  return useQuery({
    queryKey: ['slot-disponibili', operatore, servizio, data],
    queryFn: () => fetchSlotDisponibili(operatore, servizio, data),
    enabled: !!(operatore && servizio && data),
  })
}

export function useCreaPrenotazione() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (dati: PrenotazioneInput) => prenotazioneApi.crea(dati),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_PRENOTAZIONI }),
  })
}

export function useCancellaPrenotazione() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: cancellaPrenotazione,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_PRENOTAZIONI }),
  })
}

export function useSegnaPresenza() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, stato_presenza }: { id: string; stato_presenza: StatoPresenza }) =>
      segnaPresenza(id, stato_presenza),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_PRENOTAZIONI }),
  })
}

export function useAggiornaPagamento() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, stato_pagamento }: { id: string; stato_pagamento: StatoPagamento }) =>
      prenotazioneApi.aggiorna(id, { stato_pagamento } as Partial<PrenotazioneInput>),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_PRENOTAZIONI }),
  })
}
