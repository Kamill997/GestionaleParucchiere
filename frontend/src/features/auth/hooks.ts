import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { ApiError } from '@/lib/api'

import {
  aggiornaProfilo,
  cambiaPassword,
  confermaResetPassword,
  ensureCsrfCookie,
  fetchMe,
  login,
  logout,
  register,
  type RegisterPayload,
  richiediResetPassword,
  fetchSessioni,
  revocaSessione,
  revocaAltreSessioni,
  revocaTutteSessioni,
} from './api'

export const authQueryKey = ['auth', 'me'] as const

/**
 * L'utente corrente e' stato server (fetch da /auth/me/), quindi vive in
 * TanStack Query e non in uno store Zustand (vedi docs/01-frontend.md:
 * Zustand e' riservato allo stato client puro).
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: authQueryKey,
    queryFn: fetchMe,
    retry: false,
    staleTime: 5 * 60 * 1000,
    // 401 e' l'esito normale per un visitatore non loggato, non un errore
    // da ritentare o segnalare in UI.
    throwOnError: (error) => !(error instanceof ApiError && error.status === 401),
  })
}

export function useLogin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      await ensureCsrfCookie()
      return login(email, password)
    },
    onSuccess: (user) => {
      queryClient.setQueryData(authQueryKey, user)
    },
  })
}

export function useRegister() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: RegisterPayload) => {
      await ensureCsrfCookie()
      return register(payload)
    },
    onSuccess: (user) => {
      queryClient.setQueryData(authQueryKey, user)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: logout,
    onSettled: () => {
      queryClient.setQueryData(authQueryKey, null)
      queryClient.clear()
      navigate('/login', { replace: true })
    },
  })
}

export function useAggiornaProfilo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: aggiornaProfilo,
    onSuccess: (user) => {
      queryClient.setQueryData(authQueryKey, user)
    },
  })
}

export function useCambiaPassword() {
  return useMutation({
    mutationFn: cambiaPassword,
  })
}

export function useRichiediResetPassword() {
  return useMutation({
    mutationFn: richiediResetPassword,
  })
}

export function useConfermaResetPassword() {
  return useMutation({
    mutationFn: confermaResetPassword,
  })
}

export const sessioniQueryKey = ['auth', 'sessioni'] as const

export function useSessioniUtente() {
  return useQuery({
    queryKey: sessioniQueryKey,
    queryFn: fetchSessioni,
  })
}

export function useRevocaSessione() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: revocaSessione,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sessioniQueryKey })
    },
  })
}

export function useRevocaAltreSessioni() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: revocaAltreSessioni,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sessioniQueryKey })
    },
  })
}

export function useRevocaTutteSessioni() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: revocaTutteSessioni,
    onSettled: () => {
      queryClient.setQueryData(authQueryKey, null)
      queryClient.clear()
      navigate('/login', { replace: true })
    },
  })
}

