import { apiClient } from '@/shared/api/client'
import type { AuthUser } from '@/modules/auth/types/auth'

// Cloud /users (camelCase). No roles yet: every account is ADMIN with full access.
export const userService = {
  list: () => apiClient.get<AuthUser[]>('/users'),
  create: (payload: { username: string; email: string; password: string; displayName?: string }) =>
    apiClient.post<AuthUser>('/users', payload),
  get: (userId: string) => apiClient.get<AuthUser>(`/users/${userId}`),
  update: (userId: string, payload: { displayName?: string; status?: AuthUser['status']; password?: string }) =>
    apiClient.patch<AuthUser>(`/users/${userId}`, payload),
}
