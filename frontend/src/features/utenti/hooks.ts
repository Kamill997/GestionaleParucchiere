import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { creaClientRisorsa } from '@/lib/api'

import type { UtenteAdmin, UtenteAdminInput } from './types'

const CHIAVE_UTENTI = ['utenti-admin'] as const

const utenteAdminApi = creaClientRisorsa<UtenteAdmin, UtenteAdminInput>('/admin/utenti/')

/**
 * Gestione utenti/ruoli (docs/03-componenti-e-workflow.md: "CRUD utenti,
 * assegnazione ruoli/permessi"). L'endpoint e' quello nato in Fase 2 come
 * dimostrazione del guard RBAC, esteso in Fase 4 a CRUD completo.
 */
export function useUtentiAdmin(pagina = 1) {
  return useQuery({
    queryKey: [...CHIAVE_UTENTI, pagina],
    queryFn: () => utenteAdminApi.lista(`?page=${pagina}&page_size=100`),
  })
}

export function useCreaUtenteAdmin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (dati: UtenteAdminInput) => utenteAdminApi.crea(dati),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_UTENTI }),
  })
}

export function useAggiornaUtenteAdmin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, dati }: { id: string; dati: Partial<UtenteAdminInput> }) =>
      utenteAdminApi.aggiorna(id, dati),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_UTENTI }),
  })
}
