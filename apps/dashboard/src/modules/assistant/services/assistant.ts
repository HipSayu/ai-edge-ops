import { apiClient, authStorage } from '@/shared/api/client'
import type { ChatMessage, ChatStreamEvent, ToolDecision } from '@/modules/assistant/types/assistant'

// Assistant API (apps/assistant), behind the dashboard nginx at /api/v1/chat:
//   POST /chat/stream { session_id, message } → { stream_id }, then GET /chat/stream/{stream_id} (SSE)
//   POST /chat/{session_id}/approval { decisions } → { stream_id } resumes a turn paused on write tools
// Saved conversations (list, messages) are the Cloud's: services/conversations.ts.
const WIDGET_SESSION_KEY = 'av_assistant_session'
const API_BASE_URL = (import.meta.env.VITE_API_URL ?? '/api/v1').replace(/\/$/, '')

const widgetSessionId = () => {
  let id = localStorage.getItem(WIDGET_SESSION_KEY)
  if (!id) {
    // crypto.randomUUID only exists in secure contexts (HTTPS / localhost); the dashboard may be served over HTTP
    id = typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : Array.from(crypto.getRandomValues(new Uint8Array(16)), (b) => b.toString(16).padStart(2, '0')).join('')
    localStorage.setItem(WIDGET_SESSION_KEY, id)
  }
  return id
}

type StreamCreated = { stream_id: string; session_id: string }

/** Reads an SSE body frame by frame. EventSource can't send the Authorization header, hence fetch. */
async function* readStream(streamId: string, signal?: AbortSignal): AsyncGenerator<ChatStreamEvent> {
  const token = authStorage.getAccessToken()
  const response = await fetch(`${API_BASE_URL}/chat/stream/${streamId}`, {
    headers: { Accept: 'text/event-stream', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    signal,
  })
  if (!response.ok || !response.body) throw new Error(`Chat stream failed with status ${response.status}`)

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) return
    buffer += value
    let end: number
    while ((end = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, end)
      buffer = buffer.slice(end + 2)
      let event = 'message'
      const data: string[] = []
      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) data.push(line.slice(5).trimStart())
      }
      if (data.length) yield { event, data: JSON.parse(data.join('\n')) } as ChatStreamEvent
    }
  }
}

export const assistantService = {
  /** Non-streaming turn, for the compact assistant panel (its own session, not a saved conversation). */
  sendMessage: async (text: string): Promise<ChatMessage> => {
    const reply = await apiClient.post<{ session_id: string; answer: string }>('/chat', { session_id: widgetSessionId(), message: text })
    return { id: Date.now(), role: 'assistant', text: reply.answer, timestamp: new Date().toISOString() }
  },

  /** One turn in a conversation: its id is the assistant session holding the agent's memory. */
  streamMessage: async function* (sessionId: string, text: string, signal?: AbortSignal) {
    const created = await apiClient.post<StreamCreated>('/chat/stream', { session_id: sessionId, message: text })
    yield* readStream(created.stream_id, signal)
  },

  streamApproval: async function* (sessionId: string, decisions: ToolDecision[], signal?: AbortSignal) {
    const created = await apiClient.post<StreamCreated>(`/chat/${sessionId}/approval`, { decisions })
    yield* readStream(created.stream_id, signal)
  },
}
