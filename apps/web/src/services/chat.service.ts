import { api, tokenStore } from '@/api/client'
import { streamChat } from '@/api/sse'
import type { ChatEvent } from '@/api/types'

export const chatService = {
  stream: (
    message: string,
    sessionId: string | null,
    onEvent: (event: ChatEvent) => void,
    signal: AbortSignal,
    options?: { model?: string; imageIds?: string[] },
  ) => streamChat(message, sessionId, onEvent, signal, options),
  // The models the user may pick, and the default one
  models: () => api.get<{ default: string; models: string[] }>('/chat/models'),
  // Attaches a picture to send with the next message; returns its id
  uploadImage: async (file: File): Promise<string> => {
    const form = new FormData()
    form.append('file', file)
    const response = await fetch('/api/chat/images', {
      method: 'POST',
      headers: { Authorization: `Bearer ${tokenStore.get() ?? ''}` },
      body: form,
    })
    if (!response.ok) {
      const detail = (await response.json().catch(() => null))?.detail
      throw new Error(typeof detail === 'string' ? detail : `Could not upload the image (${response.status})`)
    }
    return ((await response.json()) as { image_id: string }).image_id
  },
  // The user's decision on a change the assistant proposed; the server applies it
  decide: (proposalId: string, approve: boolean) =>
    api.post<{ message: string }>(`/chat/approvals/${proposalId}`, { approve }),
}
