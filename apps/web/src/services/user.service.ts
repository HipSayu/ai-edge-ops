import { api } from '@/api/client'
import type { User, UserInput } from '@/api/types'

export const userService = {
  list: () => api.get<User[]>('/users'),
  create: (input: UserInput) => api.post<User>('/users', input),
  update: (id: number, input: Partial<UserInput>) => api.put<User>(`/users/${id}`, input),
  remove: (id: number) => api.del<void>(`/users/${id}`),
}
