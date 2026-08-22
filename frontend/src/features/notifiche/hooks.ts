import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useCurrentUser } from '@/features/auth/hooks'

import { fetchNonLetteCount, notificaApi, segnaLetta, segnaTutteLette } from './api'

const CHIAVE_NOTIFICHE = ['notifiche'] as const

export function useNotifiche(abilitato: boolean) {
  return useQuery({
    queryKey: CHIAVE_NOTIFICHE,
    queryFn: () => notificaApi.lista('?page_size=20'),
    enabled: abilitato,
  })
}

/**
 * Polling leggero (60s) per il badge non lette: le notifiche non sono
 * cosi' urgenti da giustificare WebSocket in questa prima versione (vedi
 * docs/02-backend.md, "Django Channels (opzionale) se serve WebSocket" -
 * non ancora necessario).
 */
export function useNonLetteCount() {
  const { data: user } = useCurrentUser()
  return useQuery({
    queryKey: [...CHIAVE_NOTIFICHE, 'non-lette-count'],
    queryFn: fetchNonLetteCount,
    enabled: !!user,
    refetchInterval: 60 * 1000,
    select: (dati) => dati.conteggio,
  })
}

export function useSegnaLetta() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: segnaLetta,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_NOTIFICHE }),
  })
}

export function useSegnaTutteLette() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: segnaTutteLette,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHIAVE_NOTIFICHE }),
  })
}
