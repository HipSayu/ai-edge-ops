import { tokenStore, ApiError } from '@/api/client'
import type { ChatEvent } from '@/api/types'

// A chat is two calls: POST /api/chat starts the turn and answers with a stream id, GET /api/chat/stream/{id} carries the
// events as the model writes them. Read with fetch, not EventSource, because the request needs an Authorization header.
export async function streamChat(
  message: string,
  sessionId: string | null,
  onEvent: (event: ChatEvent) => void,
  signal: AbortSignal,
  options: { model?: string; imageIds?: string[] } = {},
): Promise<void> {
  const headers = { Authorization: `Bearer ${tokenStore.get() ?? ''}` }
  const started = await fetch('/api/chat', {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, model: options.model, image_ids: options.imageIds ?? [] }),
    signal,
  })
  if (!started.ok) throw new ApiError(await detailOf(started), started.status)
  const { stream_id } = (await started.json()) as { stream_id: string }
  const response = await fetch(`/api/chat/stream/${stream_id}`, { headers, signal })
  if (!response.ok || !response.body) throw new ApiError(await detailOf(response), response.status)

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      const parsed = parseFrame(frame)
      if (parsed) onEvent(parsed)
      boundary = buffer.indexOf('\n\n')
    }
  }
}

async function detailOf(response: Response): Promise<string> {
  try {
    const data = await response.json()
    if (typeof data?.detail === 'string') return data.detail
  } catch {
    /* not JSON */
  }
  return `Lỗi ${response.status}`
}

function parseFrame(frame: string): ChatEvent | null {
  let name = ''
  const data: string[] = []
  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) name = line.slice(6).trim()
    else if (line.startsWith('data:')) data.push(line.slice(5).trim())
  }
  if (!name || data.length === 0) return null
  try {
    return { type: name, ...JSON.parse(data.join('\n')) } as ChatEvent
  } catch {
    return null
  }
}
