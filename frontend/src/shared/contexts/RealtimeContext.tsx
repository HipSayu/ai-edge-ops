import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { authStorage } from '@/shared/api/client'

type RealtimeChannel = 'telemetry' | 'alerts' | 'logs'
export type RealtimeEnvelope<T = unknown> = {
  type: string
  source: string
  payload: T
}
type MessageHandler = (message: RealtimeEnvelope) => void

type ChannelState = {
  status: 'idle' | 'connecting' | 'open' | 'closed'
  socket: WebSocket | null
  handlers: Set<MessageHandler>
  reconnectTimer: number | null
  reconnectAttempts: number
}

type RealtimeContextValue = {
  subscribe: (channel: RealtimeChannel, handler: MessageHandler) => () => void
  status: (channel: RealtimeChannel) => ChannelState['status']
}

const RealtimeContext = createContext<RealtimeContextValue | null>(null)

const channels: RealtimeChannel[] = ['telemetry', 'alerts', 'logs']

function websocketUrl(channel: RealtimeChannel): string {
  const apiBase = (import.meta.env.VITE_API_URL ?? '/api/v1').replace(/\/$/, '')
  const base = new URL(apiBase, window.location.origin)
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'

  const suffix = channel === 'telemetry' ? '/agent/ws/telemetry' : channel === 'logs' ? '/agent/ws/logs' : '/ws/alerts'
  base.pathname = `${base.pathname}${suffix}`.replace(/\/+/g, '/')
  // Browsers can't set headers on `new WebSocket`, so the access token rides
  // as a query param (see backend app/core/ws_auth.py).
  const token = authStorage.getAccessToken()
  if (token) base.searchParams.set('token', token)
  return base.toString()
}

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const states = useRef<Record<RealtimeChannel, ChannelState>>(
    Object.fromEntries(
      channels.map((channel) => [channel, { status: 'idle', socket: null, handlers: new Set(), reconnectTimer: null, reconnectAttempts: 0 }]),
    ) as Record<RealtimeChannel, ChannelState>,
  )
  const [version, rerender] = useState(0)

  useEffect(() => {
    return () => {
      channels.forEach((channel) => {
        const state = states.current[channel]
        if (state.reconnectTimer !== null) window.clearTimeout(state.reconnectTimer)
        state.socket?.close()
      })
    }
  }, [])

  const connect = useCallback((channel: RealtimeChannel) => {
    const state = states.current[channel]
    if (state.socket || state.handlers.size === 0) return

    state.status = 'connecting'
    rerender((value) => value + 1)
    const socket = new WebSocket(websocketUrl(channel))
    state.socket = socket

    socket.onopen = () => {
      state.status = 'open'
      state.reconnectAttempts = 0
      rerender((value) => value + 1)
      // Ask the server to replay current state so the UI isn't blank until the
      // next push (telemetry snapshot-on-connect; harmless on other channels).
      try {
        socket.send(JSON.stringify({ op: 'snapshot' }))
      } catch {
        // socket not ready — the next reconnect will retry
      }
    }
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as RealtimeEnvelope
        state.handlers.forEach((handler) => handler(message))
      } catch {
        // Ignore malformed frames so one bad message cannot kill the stream.
      }
    }
    socket.onerror = () => socket.close()
    socket.onclose = () => {
      state.socket = null
      state.status = state.handlers.size > 0 ? 'closed' : 'idle'
      rerender((value) => value + 1)
      if (state.handlers.size > 0) {
        const delay = Math.min(500 * 2 ** state.reconnectAttempts, 8000)
        state.reconnectAttempts += 1
        state.reconnectTimer = window.setTimeout(() => {
          state.reconnectTimer = null
          connect(channel)
        }, delay)
      }
    }
  }, [])

  const subscribe = useCallback((channel: RealtimeChannel, handler: MessageHandler) => {
    const state = states.current[channel]
    state.handlers.add(handler)
    connect(channel)

    return () => {
      state.handlers.delete(handler)
      if (state.handlers.size === 0) {
        if (state.reconnectTimer !== null) window.clearTimeout(state.reconnectTimer)
        state.reconnectTimer = null
        state.socket?.close()
        state.socket = null
        state.status = 'idle'
        rerender((value) => value + 1)
      }
    }
  }, [connect])

  const value = useMemo<RealtimeContextValue>(() => ({
    subscribe,
    status: (channel) => states.current[channel].status,
  }), [subscribe, version])

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>
}

export function useRealtimeChannel(channel: RealtimeChannel, handler: MessageHandler) {
  const context = useContext(RealtimeContext)
  if (!context) throw new Error('useRealtimeChannel must be used inside RealtimeProvider')

  useEffect(() => context.subscribe(channel, handler), [channel, context.subscribe, handler])
  return context.status(channel)
}
