import { apiClient } from '../client'
import type { ChatMessage } from '../types/assistant'

export const assistantService = {
  listMessages: () => apiClient.get<ChatMessage[]>('/assistant/messages'),
  sendMessage: (text: string) => apiClient.post<ChatMessage>('/assistant/messages', { text }),
}
