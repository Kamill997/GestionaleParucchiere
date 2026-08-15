import { apiFetch } from '@/lib/api'

import type { User } from './types'

export function ensureCsrfCookie() {
  return apiFetch<{ detail: string }>('/auth/csrf/')
}

export function login(email: string, password: string) {
  return apiFetch<User>('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function logout() {
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
