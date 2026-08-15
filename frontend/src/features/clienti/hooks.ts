import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { clienteApi, importaClienti } from './api'
import type { ClienteInput } from './types'

const CHIAVE_CLIENTI = ['clienti'] as const

export function useClienti(pagina: number, ricerca = '') {
  const params = new URLSearchParams({ page: String(pagina) })
  if (ricerca) params.set('search', ricerca)

  return useQuery({
    queryKey: [...CHIAVE_CLIENTI, pagina, ricerca],
    queryFn: () => clienteApi.lista(`?${params.toString()}`),
  })
}

export function useCreaCliente() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (dati: ClienteInput) => clienteApi.crea(dati),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_CLIENTI }),
  })
}

export function useAggiornaCliente() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, dati }: { id: string; dati: Partial<ClienteInput> }) =>
      clienteApi.aggiorna(id, dati),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_CLIENTI }),
  })
}

// docs/07-import-export-dati.md: dopo un import in blocco la lista corrente
// va invalidata come per crea/aggiorna singoli, cosi' le righe nuove o
// aggiornate compaiono subito senza bisogno di un refresh manuale.
export function useImportaClienti() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => importaClienti(file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_CLIENTI }),
  })
}
