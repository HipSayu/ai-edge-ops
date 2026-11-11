import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { tokenStore } from '@/api/client'
import type { Role, User } from '@/api/types'
import { authService } from '@/services/auth.service'

interface AuthState {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isAdmin: boolean
  canOperate: boolean // OPERATOR or ADMIN: export reports, upload videos
}

const AuthContext = createContext<AuthState | null>(null)
const RANK: Record<Role, number> = { VIEWER: 0, OPERATOR: 1, ADMIN: 2 }

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => tokenStore.get() !== null)

  useEffect(() => {
    if (!tokenStore.get()) return
    authService
      .me()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const result = await authService.login(username, password)
    tokenStore.set(result.access_token)
    setUser(result.user)
  }, [])

  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      user, loading, login, logout,
      isAdmin: user?.role === 'ADMIN',
      canOperate: user !== null && RANK[user.role] >= RANK.OPERATOR,
    }),
    [user, loading, login, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
