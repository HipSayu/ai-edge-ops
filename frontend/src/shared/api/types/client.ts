export interface AuthTokens {
  accessToken: string
  refreshToken: string
}

export type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
  query?: Record<string, string | number | boolean | null | undefined>
}

export type ApiEnvelope<T> = {
  success: boolean
  data: T
  error?: unknown
  request_id?: string
}
