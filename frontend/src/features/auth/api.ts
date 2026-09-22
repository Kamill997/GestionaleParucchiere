import { apiFetch, setCsrfToken } from '@/lib/api'

import type { User, UserSession } from './types'

export async function ensureCsrfCookie() {
  try {
    const data = await apiFetch<{ csrfToken?: string; detail: string }>('/auth/csrf/')
    if (data && typeof data === 'object' && data.csrfToken) {
      setCsrfToken(data.csrfToken)
    }
    return data
  } catch {
    return { detail: 'Cookie CSRF impostato.' }
  }
}

export function login(email: string, password: string) {
  return apiFetch<User>('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function logout() {
  await ensureCsrfCookie().catch(() => {})
  return apiFetch<{ detail: string }>('/auth/logout/', { method: 'POST' })
}

export function fetchMe() {
  return apiFetch<User>('/auth/me/')
}

export interface RegisterPayload {
  email: string
  password: string
  nome?: string
  cognome?: string
  telefono?: string
}

export function register(payload: RegisterPayload) {
  return apiFetch<User>('/auth/register/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function aggiornaProfilo(payload: { nome?: string; cognome?: string; telefono?: string }) {
  return apiFetch<User>('/auth/me/', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function cambiaPassword(payload: { vecchia_password: string; nuova_password: string }) {
  return apiFetch<{ detail: string }>('/auth/change-password/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function richiediResetPassword(email: string) {
  return apiFetch<{ detail: string }>('/auth/password-reset/', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
}

export function confermaResetPassword(payload: {
  uid: string
  token: string
  nuova_password: string
}) {
  return apiFetch<{ detail: string }>('/auth/password-reset-confirm/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchSessioni() {
  return apiFetch<UserSession[]>('/auth/sessioni/')
}

export async function revocaSessione(id: string) {
  await ensureCsrfCookie()
  return apiFetch<{ detail: string }>(`/auth/sessioni/${id}/revoca/`, {
    method: 'POST',
  })
}

export async function revocaAltreSessioni() {
  await ensureCsrfCookie()
  return apiFetch<{ detail: string }>('/auth/sessioni/revoca-altre/', {
    method: 'POST',
  })
}

export async function revocaTutteSessioni() {
  await ensureCsrfCookie()
  return apiFetch<{ detail: string }>('/auth/sessioni/revoca-tutte/', {
    method: 'POST',
  })
}

