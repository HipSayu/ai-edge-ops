import type { ApiEnvelope, AuthTokens, RequestOptions } from '@/shared/api/types'
export type { AuthTokens } from '@/shared/api/types'

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? '/api/v1').replace(/\/$/, '')
const ACCESS_TOKEN_KEY = 'av_access_token'
const REFRESH_TOKEN_KEY = 'av_refresh_token'

export const authStorage = {
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (tokens: AuthTokens) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken)
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

export class ApiError extends Error {
  readonly status: number
  readonly details: unknown

  constructor(message: string, status: number, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

function buildUrl(path: string, query?: RequestOptions['query']) {
  const url = new URL(`${API_BASE_URL}/${path.replace(/^\//, '')}`, window.location.origin)

  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null) url.searchParams.set(key, String(value))
  })

  return url
}

async function parseResponse(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined

  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) return response.json()
  return response.text()
}

// Refresh tokens are single-use: concurrent 401s must share one refresh call.
let pendingRefresh: Promise<AuthTokens> | null = null

function refreshOnce(refreshToken: string): Promise<AuthTokens> {
  pendingRefresh ??= request<AuthTokens>('/auth/refresh', { method: 'POST', body: { refreshToken } }).finally(() => {
    pendingRefresh = null
  })
  return pendingRefresh
}

/** The session cannot be refreshed: back to the sign-in page (HashRouter). */
function onSessionExpired() {
  if (!window.location.hash.startsWith('#/login')) window.location.hash = '#/login'
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, query, headers, ...init } = options
  const accessToken = authStorage.getAccessToken()
  const response = await fetch(buildUrl(path, query), {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const payload = await parseResponse(response)

  if (response.status === 401 && !path.startsWith('/auth/')) {
    const refreshToken = authStorage.getRefreshToken()
    if (refreshToken) {
      try {
        const refreshed = await refreshOnce(refreshToken)
        authStorage.setTokens(refreshed)
        return request<T>(path, options)
      } catch {
        // fall through to sign-out below
      }
    }
    authStorage.clear()
    onSessionExpired()
  }

  if (!response.ok) {
    const message =
      typeof payload === 'object' && payload !== null && 'message' in payload
        ? String(payload.message)
        : `API request failed with status ${response.status}`
    throw new ApiError(message, response.status, payload)
  }

  if (
    typeof payload === 'object' &&
    payload !== null &&
    'success' in payload &&
    'data' in payload
  ) {
    return (payload as ApiEnvelope<T>).data
  }

  return payload as T
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'POST', body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'DELETE' }),
}
