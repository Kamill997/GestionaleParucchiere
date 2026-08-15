import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { operatoreApi } from './api'
import type { OperatoreInput } from './types'

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
