import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  creaEccezione,
  eliminaEccezione,
  fetchDisponibilitaOperatore,
  fetchEccezioni,
  operatoreApi,
  salvaTurniSettimana,
} from './api'
import type {
  EccezioneDisponibilitaInput,
  GiornoTurnoInput,
  OperatoreInput,
} from './types'

const CHIAVE_OPERATORI = ['operatori'] as const

export function useOperatori(pagina = 1, soloAttivi = false) {
  const params = new URLSearchParams({ page: String(pagina) })
  if (soloAttivi) params.set('attivo', 'true')

  return useQuery({
    queryKey: [...CHIAVE_OPERATORI, pagina, soloAttivi],
    queryFn: () => operatoreApi.lista(`?${params.toString()}`),
  })
}

export function useCreaOperatore() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (dati: OperatoreInput) => operatoreApi.crea(dati),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_OPERATORI }),
  })
}

export function useAggiornaOperatore() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, dati }: { id: string; dati: Partial<OperatoreInput> }) =>
      operatoreApi.aggiorna(id, dati),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_OPERATORI }),
  })
}

export function useEliminaOperatore() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => operatoreApi.elimina(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_OPERATORI }),
  })
}

const CHIAVE_DISPONIBILITA = ['disponibilita'] as const

export function useDisponibilitaOperatore(operatoreId: string | null) {
  return useQuery({
    queryKey: [...CHIAVE_DISPONIBILITA, operatoreId],
    queryFn: () => (operatoreId ? fetchDisponibilitaOperatore(operatoreId) : null),
    enabled: !!operatoreId,
  })
}

export function useSalvaTurniSettimana() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      operatoreId,
      giorni,
    }: {
      operatoreId: string
      giorni: GiornoTurnoInput[]
    }) => salvaTurniSettimana(operatoreId, giorni),
    onSuccess: (_, { operatoreId }) => {
      queryClient.invalidateQueries({ queryKey: [...CHIAVE_DISPONIBILITA, operatoreId] })
      queryClient.invalidateQueries({ queryKey: ['slot-disponibili'] })
    },
  })
}

const CHIAVE_ECCEZIONI = ['eccezioni-disponibilita'] as const

export function useEccezioni(params?: Record<string, string | undefined>) {
  return useQuery({
    queryKey: [...CHIAVE_ECCEZIONI, params],
    queryFn: () => fetchEccezioni(params),
  })
}

export function useCreaEccezione() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (dati: EccezioneDisponibilitaInput) => creaEccezione(dati),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHIAVE_ECCEZIONI })
      queryClient.invalidateQueries({ queryKey: ['slot-disponibili'] })
      queryClient.invalidateQueries({ queryKey: ['prenotazioni-calendario'] })
    },
  })
}

export function useEliminaEccezione() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => eliminaEccezione(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHIAVE_ECCEZIONI })
      queryClient.invalidateQueries({ queryKey: ['slot-disponibili'] })
      queryClient.invalidateQueries({ queryKey: ['prenotazioni-calendario'] })
    },
  })
}

