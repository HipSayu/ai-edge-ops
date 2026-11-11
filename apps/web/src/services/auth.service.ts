import { api } from '@/api/client'
import type { LoginResult, User } from '@/api/types'

export const authService = {
  login: (username: string, password: string) => api.post<LoginResult>('/auth/login', { username, password }),
  me: () => api.get<User>('/auth/me'),
}
