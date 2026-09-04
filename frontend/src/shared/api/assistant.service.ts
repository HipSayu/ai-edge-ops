import type { ChatMessage } from '@/modules/observability/mock/incidents'
import { apiClient } from './client'

export const assistantService = {
  listMessages: () => apiClient.get<ChatMessage[]>('/assistant/messages'),
  sendMessage: (text: string) => apiClient.post<ChatMessage>('/assistant/messages', { text }),
}
