import type { UserAccount } from '@/modules/system/mock/system'
import { apiClient, authStorage, type AuthTokens } from './client'

export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthSession extends AuthTokens {
  user: UserAccount
}

export const authService = {
  async login(credentials: LoginCredentials) {
    const session = await apiClient.post<AuthSession>('/auth/login', credentials)
    authStorage.setTokens(session)
    return session
  },

  async refresh() {
    const refreshToken = authStorage.getRefreshToken()
    if (!refreshToken) throw new Error('No refresh token available')

    const tokens = await apiClient.post<AuthTokens>('/auth/refresh', { refreshToken })
    authStorage.setTokens(tokens)
    return tokens
  },

  async getCurrentUser() {
    return apiClient.get<UserAccount>('/auth/me')
  },

  async logout() {
    try {
      await apiClient.post<void>('/auth/logout')
    } finally {
      authStorage.clear()
    }
  },

  isAuthenticated: () => Boolean(authStorage.getAccessToken()),
}
