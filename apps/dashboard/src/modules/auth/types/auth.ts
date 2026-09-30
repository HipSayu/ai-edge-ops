import type { AuthTokens } from '@/shared/api/types'

export type { AuthTokens } from '@/shared/api/types'

export type UserRole = 'ADMIN' | 'OPERATOR' | 'VIEWER'

/** The signed-in account, as returned by the Cloud /auth endpoints. */
export interface AuthUser {
  id: string
  username: string
  email: string
  displayName: string | null
  role: UserRole
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED'
  createdAt: string | null
  lastLoginAt: string | null
}

export interface LoginCredentials {
  /** Email or username */
  login: string
  password: string
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
  displayName?: string
}

export interface AuthSession extends AuthTokens {
  tokenType: string
  expiresIn: number
  user: AuthUser
}
