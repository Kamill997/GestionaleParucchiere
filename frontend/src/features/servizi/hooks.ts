import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { servizioApi } from './api'
import type { ServizioInput } from './types'

const CHIAVE_SERVIZI = ['servizi'] as const

export function useServizi(pagina: number, categoria?: string) {
  const params = new URLSearchParams({ page: String(pagina) })
  if (categoria) params.set('categoria', categoria)

  return useQuery({
    queryKey: [...CHIAVE_SERVIZI, pagina, categoria],
    queryFn: () => servizioApi.lista(`?${params.toString()}`),
  })
}

export function useCreaServizio() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (dati: ServizioInput) => servizioApi.crea(dati),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_SERVIZI }),
  })
}

export function useAggiornaServizio() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, dati }: { id: string; dati: Partial<ServizioInput> }) =>
      servizioApi.aggiorna(id, dati),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_SERVIZI }),
  })
}

export function useEliminaServizio() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => servizioApi.elimina(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_SERVIZI }),
  })
}
