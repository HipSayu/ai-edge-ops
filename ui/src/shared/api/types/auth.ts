import type { AuthTokens } from './client'
import type { UserAccount } from './user'

export type { AuthTokens } from './client'

export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthSession extends AuthTokens {
  user: UserAccount
}
