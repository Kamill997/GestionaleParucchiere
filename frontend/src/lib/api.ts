const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown, message?: string) {
    super(message ?? `Richiesta API fallita con status ${status}`)
    this.status = status
    this.body = body
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

let inMemoryCsrfToken: string | null = null

export function setCsrfToken(token: string | null) {
  inMemoryCsrfToken = token
}

export function getCsrfToken(): string | null {
  return inMemoryCsrfToken ?? readCookie('csrftoken')
}

/**
 * Wrapper fetch: sempre credentials:'include' (i token JWT sono in cookie
 * httpOnly, vedi backend/common/authentication.py), header X-CSRFToken
 * automatico sui metodi mutanti (richiede aver chiamato ensureCsrfCookie()
 * almeno una volta, vedi features/auth/api.ts).
 */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? 'GET').toUpperCase()
  const headers = new Headers(init.headers)

  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (MUTATING_METHODS.has(method)) {
    const csrfToken = getCsrfToken()
    if (csrfToken) headers.set('X-CSRFToken', csrfToken)
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    method,
    headers,
    credentials: 'include',
  })

  if (response.status === 204) {
    return undefined as T
  }

  const isJson = response.headers.get('content-type')?.includes('application/json')
  const body = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    throw new ApiError(response.status, body)
  }

  return body as T
}

export interface RisultatoPaginato<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/**
 * Helper CRUD generici per un endpoint REST standard (list/retrieve/create/
 * update/delete), cosi' ogni feature (Servizi, Operatori...) non riscrive
 * le stesse funzioni fetch (vedi docs/03-componenti-e-workflow.md, "Modulo
 * Anagrafiche come CRUD generico riusabile").
 */
export function creaClientRisorsa<T, TInput = Partial<T>>(percorsoBase: string) {
  return {
    lista: (queryString = '') => apiFetch<RisultatoPaginato<T>>(`${percorsoBase}${queryString}`),
    dettaglio: (id: string) => apiFetch<T>(`${percorsoBase}${id}/`),
    crea: (dati: TInput) =>
      apiFetch<T>(percorsoBase, { method: 'POST', body: JSON.stringify(dati) }),
    aggiorna: (id: string, dati: Partial<TInput>) =>
      apiFetch<T>(`${percorsoBase}${id}/`, { method: 'PATCH', body: JSON.stringify(dati) }),
    elimina: (id: string) => apiFetch<void>(`${percorsoBase}${id}/`, { method: 'DELETE' }),
  }
}
