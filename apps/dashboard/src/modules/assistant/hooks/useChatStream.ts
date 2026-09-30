import { useCallback, useEffect, useRef, useState } from 'react'
import { assistantService } from '@/modules/assistant/services/assistant'
import { conversationService } from '@/modules/assistant/services/conversations'
import type { ChatStreamEvent, PendingApproval, StoredMessage, ToolDecision, TraceStep } from '@/modules/assistant/types/assistant'

export interface ChatTurnMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  trace: TraceStep[]
  streaming?: boolean
  error?: boolean
  approval?: PendingApproval
  startedAt?: number
  finishedAt?: number
}

const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

/** Appends streamed text to the last trace step when it is of the same kind, else starts a new step. */
function appendText(trace: TraceStep[], kind: 'reasoning' | 'text', text: string): TraceStep[] {
  const last = trace[trace.length - 1]
  if (last && last.kind === kind) return [...trace.slice(0, -1), { ...last, text: last.text + text }]
  return [...trace, { kind, text }]
}

/** Applies one SSE event to the assistant message being streamed. Text streamed in a round that goes on to
 *  call tools is the agent working out loud: it moves into the trace, and `done.reply` is the answer. */
function apply(message: ChatTurnMessage, e: ChatStreamEvent): ChatTurnMessage {
  switch (e.event) {
    case 'reasoning':
      return { ...message, trace: appendText(message.trace, 'reasoning', e.data.content) }
    case 'token':
      return { ...message, content: message.content + e.data.content }
    case 'status': {
      const said = message.content.trim()
      const trace = said ? appendText(message.trace, 'text', said) : message.trace
      const calls: TraceStep[] = e.data.tools.map((t) => ({ kind: 'tool', id: t.id, tool: t.name, args: t.args, status: 'running' }))
      return { ...message, content: '', trace: [...trace, ...calls] }
    }
    case 'tool_end': {
      // Match by tool call id; fall back to the first running call of that tool
      const index = message.trace.findIndex((s) => s.kind === 'tool' && s.status === 'running' && (e.data.id ? s.id === e.data.id : s.tool === e.data.tool))
      if (index < 0) return message
      const trace = [...message.trace]
      trace[index] = { ...(trace[index] as Extract<TraceStep, { kind: 'tool' }>), status: e.data.status, output: e.data.output }
      return { ...message, trace }
    }
    case 'done':
      return { ...message, content: e.data.reply, streaming: false, finishedAt: Date.now() }
    case 'approval_required':
      return { ...message, streaming: false, finishedAt: Date.now(), approval: { sessionId: e.data.session_id, requests: e.data.requests } }
    case 'error':
      return { ...message, content: e.data.message, streaming: false, finishedAt: Date.now(), error: true }
  }
}

function fromStored(m: StoredMessage): ChatTurnMessage {
  const time = new Date(m.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return {
    id: m.id, role: m.role === 'USER' ? 'user' : 'assistant', content: m.content ?? '', timestamp: time,
    trace: m.metadata.trace ?? [], startedAt: m.metadata.startedAt, finishedAt: m.metadata.finishedAt,
    error: m.metadata.error,
  }
}

/** Chat in one saved conversation (`conversationId`; undefined = a new one, created on the first message).
 *  The Cloud keeps the conversation and its messages; the assistant streams the answer and keeps the agent's
 *  memory under the same id. */
export function useChatStream(
  conversationId: string | undefined,
  { onCreated, onChanged }: { onCreated: (id: string) => void; onChanged: () => void },
) {
  const [messages, setMessages] = useState<ChatTurnMessage[]>([])
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(false)
  const abort = useRef<AbortController | null>(null)
  const active = useRef<string | undefined>(conversationId)
  const justCreated = useRef<string | null>(null)

  useEffect(() => () => abort.current?.abort(), [])

  // Switching conversation: stop any stream and load its messages (not for the one this hook just created)
  useEffect(() => {
    active.current = conversationId
    if (conversationId && conversationId === justCreated.current) return
    abort.current?.abort()
    setMessages([])
    if (!conversationId) return
    let cancelled = false
    setLoading(true)
    conversationService.messages(conversationId)
      .then((stored) => { if (!cancelled) setMessages(stored.map(fromStored)) })
      .catch(() => undefined)
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [conversationId])

  const update = (id: string, fn: (m: ChatTurnMessage) => ChatTurnMessage) =>
    setMessages((prev) => prev.map((m) => (m.id === id ? fn(m) : m)))

  /** Streams events into the message and, once the turn ends (answer or error), saves it with its trace. */
  const consume = useCallback(async (cid: string, message: ChatTurnMessage, events: AsyncGenerator<ChatStreamEvent>) => {
    setBusy(true)
    let current = message
    const set = (next: ChatTurnMessage) => { current = next; update(next.id, () => next) }
    try {
      for await (const e of events) set(apply(current, e))
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      set({ ...current, content: `Không kết nối được trợ lý: ${(err as Error).message}`, error: true })
    } finally {
      set({ ...current, streaming: false, finishedAt: current.finishedAt ?? Date.now() })
      setBusy(false)
    }
    if (!current.approval) {
      const { trace, startedAt, finishedAt, error } = current
      await conversationService.addMessage(cid, 'ASSISTANT', current.content, { trace, startedAt, finishedAt, error }).catch(() => undefined)
      onChanged()
    }
  }, [onChanged])

  const send = useCallback(async (text: string) => {
    const userMessage: ChatTurnMessage = { id: `user-${Date.now()}`, role: 'user', content: text, timestamp: now(), trace: [] }
    const reply: ChatTurnMessage = { id: `ai-${Date.now()}`, role: 'assistant', content: '', timestamp: now(), trace: [], streaming: true, startedAt: Date.now() }
    setMessages((prev) => [...prev.map((m) => ({ ...m, approval: undefined })), userMessage, reply])
    abort.current = new AbortController()
    const signal = abort.current.signal

    let cid = active.current
    try {
      if (!cid) {
        cid = (await conversationService.create()).id
        justCreated.current = active.current = cid
        onCreated(cid)
      }
      await conversationService.addMessage(cid, 'USER', text)  // names an untitled conversation
      onChanged()
    } catch (err) {
      update(reply.id, (m) => ({ ...m, content: `Không lưu được hội thoại: ${(err as Error).message}`, error: true, streaming: false }))
      return
    }
    await consume(cid, reply, assistantService.streamMessage(cid, text, signal))
  }, [consume, onCreated, onChanged])

  /** Answers the pending write tool calls; the rest of the turn streams into the same message. */
  const decide = useCallback(async (id: string, decisions: ToolDecision[]) => {
    const cid = active.current
    const message = messages.find((m) => m.id === id)
    if (!cid || !message) return
    const resumed = { ...message, approval: undefined, streaming: true, finishedAt: undefined }
    update(id, () => resumed)
    abort.current = new AbortController()
    await consume(cid, resumed, assistantService.streamApproval(cid, decisions, abort.current.signal))
  }, [consume, messages])

  return { messages, busy, loading, send, decide }
}
