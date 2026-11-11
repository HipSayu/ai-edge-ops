import { useCallback, useEffect, useRef, useState } from 'react'
import type { ChatEvent } from '@/api/types'
import { storage } from '@/helpers/storage'
import { chatService } from '@/services/chat.service'

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  images?: string[] // ids of the pictures attached to a user's message
  reportUrl?: string
  approvals?: Approval[]
  failed?: boolean
}

// A change the assistant proposed; nothing happens until the user approves it
export interface Approval {
  id: string
  summary: string
  tool?: string // what the assistant wants to run, and with which values: shown in plain words, see helpers/proposal.ts
  args?: Record<string, unknown>
  state: 'pending' | 'approved' | 'rejected'
  result?: string
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  updated_at: string
}

const STORAGE_KEY = 'ppe_chat_sessions_history'

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [activity, setActivity] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const sessionId = useRef<string | null>(null)
  const nextId = useRef(1)
  const abort = useRef<AbortController | null>(null)

  useEffect(() => () => abort.current?.abort(), [])

  // Auto-save session messages to history
  const saveToHistory = useCallback((currentMessages: ChatMessage[], sid: string | null) => {
    if (currentMessages.length === 0) return
    const id = sid || sessionId.current || `session-${Date.now()}`
    sessionId.current = id

    const firstUserMsg = currentMessages.find((m) => m.role === 'user')?.content || 'New Conversation'
    const title = firstUserMsg.length > 35 ? firstUserMsg.slice(0, 35) + '...' : firstUserMsg

    try {
      const raw = storage.get(STORAGE_KEY)
      const list: ChatSession[] = raw ? JSON.parse(raw) : []
      const index = list.findIndex((s) => s.id === id)
      const sessionObj: ChatSession = {
        id,
        title,
        messages: currentMessages,
        updated_at: new Date().toISOString(),
      }
      if (index >= 0) {
        list[index] = sessionObj
      } else {
        list.unshift(sessionObj)
      }
      storage.set(STORAGE_KEY, JSON.stringify(list))
    } catch {}
  }, [])

  const send = useCallback(async (text: string, options: { files?: File[]; model?: string } = {}) => {
    const content = text.trim()
    if (!content || abort.current !== null) return
    const controller = new AbortController()
    abort.current = controller
    setBusy(true)

    // Pictures go up first, so the message can name them
    let imageIds: string[] = []
    try {
      imageIds = await Promise.all((options.files ?? []).map((file) => chatService.uploadImage(file)))
    } catch (e) {
      setMessages([...messages, { id: nextId.current++, role: 'assistant', content: e instanceof Error ? e.message : 'Could not upload the image', failed: true }])
      abort.current = null
      setBusy(false)
      return
    }

    const newMsgs: ChatMessage[] = [
      ...messages,
      { id: nextId.current++, role: 'user', content, images: imageIds.length ? imageIds : undefined },
      { id: nextId.current++, role: 'assistant', content: '' },
    ]
    setMessages(newMsgs)

    const onEvent = (event: ChatEvent) => {
      switch (event.type) {
        case 'tool_start':
          setActivity(event.name)
          break
        case 'tool_end':
          setActivity(null)
          break
        case 'token':
          setMessages((prev) => {
            const updated = prev.map((m, i) =>
              i === prev.length - 1 ? { ...m, content: m.content + event.content } : m
            )
            return updated
          })
          break
        case 'report':
          setMessages((prev) =>
            prev.map((m, i) => (i === prev.length - 1 ? { ...m, reportUrl: event.url } : m))
          )
          break
        case 'approval_required':
          setMessages((prev) =>
            prev.map((m, i) =>
              i === prev.length - 1
                ? { ...m, approvals: [...(m.approvals ?? []), { id: event.id, summary: event.summary, tool: event.tool, args: event.args, state: 'pending' as const }] }
                : m
            )
          )
          break
        case 'done':
          sessionId.current = event.session_id
          setMessages((prev) => {
            const finalMsgs = prev.map((m, i) =>
              i === prev.length - 1 ? { ...m, content: event.reply } : m
            )
            saveToHistory(finalMsgs, event.session_id)
            return finalMsgs
          })
          break
        case 'error':
          setMessages((prev) => {
            const finalMsgs = prev.map((m, i) =>
              i === prev.length - 1 ? { ...m, content: event.message, failed: true } : m
            )
            saveToHistory(finalMsgs, sessionId.current)
            return finalMsgs
          })
          break
      }
    }

    try {
      await chatService.stream(content, sessionId.current, onEvent, controller.signal, { model: options.model, imageIds })
    } catch (e) {
      if (!(e instanceof DOMException && e.name === 'AbortError')) {
        setMessages((prev) => {
          const finalMsgs = prev.map((m, i) =>
            i === prev.length - 1
              ? { ...m, content: e instanceof Error ? e.message : 'Message transmission failed', failed: true }
              : m
          )
          saveToHistory(finalMsgs, sessionId.current)
          return finalMsgs
        })
      }
    } finally {
      abort.current = null
      setActivity(null)
      setBusy(false)
    }
  }, [messages, saveToHistory])

  const decide = useCallback(async (messageId: number, approvalId: string, approve: boolean) => {
    const patch = (change: Partial<Approval>) =>
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? { ...m, approvals: m.approvals?.map((a) => (a.id === approvalId ? { ...a, ...change } : a)) }
            : m
        )
      )
    try {
      const { message } = await chatService.decide(approvalId, approve)
      patch({ state: approve ? 'approved' : 'rejected', result: message })
    } catch (e) {
      patch({ result: e instanceof Error ? e.message : 'Decision failed' })
    }
  }, [])

  const reset = useCallback(() => {
    abort.current?.abort()
    if (messages.length > 0) {
      saveToHistory(messages, sessionId.current)
    }
    sessionId.current = null
    setMessages([])
  }, [messages, saveToHistory])

  const loadSession = useCallback((session: ChatSession) => {
    abort.current?.abort()
    sessionId.current = session.id
    setMessages(session.messages)
  }, [])

  return { messages, activity, busy, send, decide, reset, loadSession, currentSessionId: sessionId.current }
}
