import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { ApiError } from '@/lib/api'

import { ensureCsrfCookie, fetchMe, login, logout } from './api'

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
