import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { aggiornaImpostazione, fetchImpostazioni } from './api'

const CHIAVE = ['impostazioni'] as const

export function useImpostazioni() {
  return useQuery({ queryKey: CHIAVE, queryFn: fetchImpostazioni })
}

export function useAggiornaImpostazione() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, valore }: { id: string; valore: string }) =>
      aggiornaImpostazione(id, valore),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE }),
  })
}
