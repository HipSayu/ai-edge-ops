import type { UserAccount } from '@/modules/system/mock/system'
import { apiClient } from './client'

export const userService = {
  list: () => apiClient.get<UserAccount[]>('/system/users'),
  get: (userId: string) => apiClient.get<UserAccount>(`/system/users/${userId}`),
  update: (userId: string, payload: Partial<UserAccount>) =>
    apiClient.patch<UserAccount>(`/system/users/${userId}`, payload),
}
