import { apiClient } from '../client'
import type { UserAccount } from '../types/user'

export const userService = {
  list: () => apiClient.get<UserAccount[]>('/users'),
  invite: (payload: { name: string; email: string; active?: boolean }) => apiClient.post<UserAccount>('/users', payload),
  get: (userId: string) => apiClient.get<UserAccount>(`/users/${userId}`),
  update: (userId: string, payload: Partial<UserAccount>) => apiClient.patch<UserAccount>(`/users/${userId}`, payload),
}
