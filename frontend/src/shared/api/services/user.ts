import { apiClient } from '../client'
import type { UserAccount } from '../types/user'

export const userService = {
  list: () => apiClient.get<UserAccount[]>('/users'),
  get: (userId: string) => apiClient.get<UserAccount>(`/users/${userId}`),
  update: (userId: string, payload: Partial<UserAccount>) => apiClient.patch<UserAccount>(`/users/${userId}`, payload),
}
