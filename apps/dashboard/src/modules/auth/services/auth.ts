import { apiClient, authStorage } from '@/shared/api/client'
import type { AuthSession, AuthUser, LoginCredentials, RegisterPayload } from '@/modules/auth/types/auth'

// Username/password sign-in against the Cloud (/api/v1/auth). The access token is short-lived;
// shared/api/client refreshes it with the refresh token on a 401.
const USER_KEY = 'av_user'

function startSession(session: AuthSession): AuthUser {
  authStorage.setTokens({ accessToken: session.accessToken, refreshToken: session.refreshToken })
  localStorage.setItem(USER_KEY, JSON.stringify(session.user))
  return session.user
}

function endSession() {
  authStorage.clear()
  localStorage.removeItem(USER_KEY)
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthUser> {
    return startSession(await apiClient.post<AuthSession>('/auth/login', credentials))
  },

  async register(payload: RegisterPayload): Promise<AuthUser> {
    return startSession(await apiClient.post<AuthSession>('/auth/register', payload))
  },

  async logout(): Promise<void> {
    const refreshToken = authStorage.getRefreshToken()
    try {
      if (refreshToken) await apiClient.post<void>('/auth/logout', { refreshToken })
    } finally {
      endSession()
    }
  },

  /** Re-reads the account from the Cloud (role or name may have changed). */
  async me(): Promise<AuthUser> {
    const user = await apiClient.get<AuthUser>('/auth/me')
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    return user
  },

  currentUser(): AuthUser | null {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as AuthUser) : null
  },

  isAuthenticated: () => Boolean(authStorage.getAccessToken() || authStorage.getRefreshToken()),
}
