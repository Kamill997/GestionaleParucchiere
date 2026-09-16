import { apiFetch, setCsrfToken } from '@/lib/api'

import type { User } from './types'

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
}

export function register(payload: RegisterPayload) {
  return apiFetch<User>('/auth/register/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
