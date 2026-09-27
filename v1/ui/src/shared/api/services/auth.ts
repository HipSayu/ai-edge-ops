import { apiClient, authStorage } from '../client'
import type { AuthTokens, AuthSession, LoginCredentials } from '../types/auth'
import type { UserAccount } from '../types/user'

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
  getCurrentUser: () => apiClient.get<UserAccount>('/auth/me'),
  async logout() { try { await apiClient.post<void>('/auth/logout') } finally { authStorage.clear() } },
  isAuthenticated: () => Boolean(authStorage.getAccessToken()),
}
