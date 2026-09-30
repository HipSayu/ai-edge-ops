import { apiClient } from '@/shared/api/client'
import type { Conversation, StoredMessage } from '@/modules/assistant/types/assistant'

// Cloud API: the signed-in user's assistant conversations and the messages shown in them.
// The assistant keeps only the agent's memory, under the conversation id (its session_id).
export const conversationService = {
  list: () => apiClient.get<Conversation[]>('/conversations'),
  create: (title?: string) => apiClient.post<Conversation>('/conversations', { title }),
  rename: (id: string, title: string) => apiClient.patch<Conversation>(`/conversations/${id}`, { title }),
  remove: (id: string) => apiClient.delete<void>(`/conversations/${id}`),
  messages: (id: string) => apiClient.get<StoredMessage[]>(`/conversations/${id}/messages`),
  addMessage: (id: string, role: StoredMessage['role'], content: string, metadata: StoredMessage['metadata'] = {}) =>
    apiClient.post<StoredMessage>(`/conversations/${id}/messages`, { role, content, metadata }),
}
