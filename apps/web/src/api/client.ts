import { storage } from '@/helpers/storage'

const BASE = '/api'
const TOKEN_KEY = 'ppe_token'

export const tokenStore = {
  get: () => storage.get(TOKEN_KEY),
  set: (token: string) => storage.set(TOKEN_KEY, token),
  clear: () => storage.remove(TOKEN_KEY),
}

export class ApiError extends Error {
  readonly status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type Query = Record<string, string | number | null | undefined>

function buildPath(path: string, query?: Query): string {
  const params = new URLSearchParams()
  Object.entries(query ?? {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  })
  const qs = params.toString()
  return `${BASE}${path}${qs ? `?${qs}` : ''}`
}

async function request<T>(
  method: string, path: string, opts: { body?: unknown; form?: FormData; binary?: Blob; query?: Query } = {},
): Promise<T> {
  const headers: Record<string, string> = {}
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json'

  const response = await fetch(buildPath(path, opts.query), {
    method,
    headers,
    body: opts.form ?? opts.binary ?? (opts.body !== undefined ? JSON.stringify(opts.body) : undefined),
  })

  if (response.status === 401 && token) {
    tokenStore.clear()
    window.location.pathname = '/login'
  }
  if (!response.ok) {
    let message = `Lỗi ${response.status}`
    try {
      const data = await response.json()
      if (typeof data?.detail === 'string') message = data.detail
    } catch {
      /* body is not JSON */
    }
    throw new ApiError(message, response.status)
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}

export const api = {
  get: <T>(path: string, query?: Query) => request<T>('GET', path, { query }),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, { body }),
  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, { body }),
  del: <T>(path: string) => request<T>('DELETE', path),
  upload: <T>(path: string, form: FormData) => request<T>('POST', path, { form }),
  postBinary: <T>(path: string, data: Blob) => request<T>('POST', path, { binary: data }),
}
