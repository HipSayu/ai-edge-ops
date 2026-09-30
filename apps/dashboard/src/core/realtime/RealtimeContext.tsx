/**
 * RealtimeContext — Multiplexed WebSocket pub/sub layer
 *
 * Connects to a single persistent WebSocket endpoint and dispatches
 * messages to subscribers by topic. Topics follow server conventions:
 *
 *   node:{node_id}                    — Node heartbeat & status change
 *   runtime:{node_id}:{runtime_id}    — Runtime process stdout / stderr events
 *   telemetry:{node_id}               — CPU / GPU / RAM / temp metrics
 *   alert:{node_id}                   — Safety & PPE detection alerts
 *   deployment:{node_id}              — Model deployment progress & status
 *   system                            — Global system events (connectivity, auth)
 *
 * Wildcard subscriptions: pass a topic prefix ending with ':' to receive
 * all messages whose topic starts with that prefix, e.g. 'alert:' receives
 * alerts from every node.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { authStorage } from '@/shared/api/client'
import { isEdgeFrame, toEnvelopes } from '@/core/realtime/edgeTopicAdapter'

// ─── Public Types ─────────────────────────────────────────────────────────────

/** Built-in well-known topic prefixes */
export type RealtimeTopic =
  | `node:${string}`
  | `runtime:${string}:${string}`
  | `telemetry:${string}`
  | `alert:${string}`
  | `deployment:${string}`
  | 'system'
  | string // allow arbitrary custom topics

export interface RealtimeEnvelope<T = unknown> {
  /** Server-assigned topic, matches the subscription pattern */
  topic: RealtimeTopic
  /** Event sub-type within the topic, e.g. 'status_change', 'metric', 'log' */
  type: string
  /** Source identifier (node_id, cluster_id, etc.) */
  source: string
  /** Arbitrary payload; typed by the consumer */
  payload: T
  /** ISO 8601 server timestamp */
  ts?: string
}

export type TopicHandler<T = unknown> = (message: RealtimeEnvelope<T>) => void

// Connection status for the shared WebSocket
export type ConnectionStatus = 'idle' | 'connecting' | 'open' | 'error' | 'closed'

interface RealtimeContextValue {
  /**
   * Subscribe to messages for a topic (or prefix).
   * Returns an unsubscribe function — call it in a useEffect cleanup.
   *
   * @example
   * subscribe('telemetry:node-hn-01', handler)
   * subscribe('alert:', handler)  // wildcard — all alert topics
   */
  subscribe: <T = unknown>(topic: string, handler: TopicHandler<T>) => () => void

  /** Publish a message to the server (fire-and-forget) */
  publish: (topic: RealtimeTopic, type: string, payload?: unknown) => void

  /** Current WebSocket connection status */
  connectionStatus: ConnectionStatus

  /** Human-readable reconnect attempt count */
  reconnectAttempt: number
}

// ─── Internal State ────────────────────────────────────────────────────────────

interface SocketState {
  socket: WebSocket | null
  status: ConnectionStatus
  reconnectTimer: ReturnType<typeof setTimeout> | null
  reconnectAttempts: number
  /** topic → Set<handler> */
  subscriptions: Map<string, Set<TopicHandler<unknown>>>
}

// ─── Context ───────────────────────────────────────────────────────────────────

const RealtimeContext = createContext<RealtimeContextValue | null>(null)

// ─── URL builder ───────────────────────────────────────────────────────────────

function buildWsUrl(): string {
  const apiBase = (import.meta.env.VITE_API_URL ?? '/api/v1').replace(/\/$/, '')
  const base = new URL(apiBase, window.location.origin)
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
  base.pathname = `${base.pathname}/ws`.replace(/\/+/g, '/')
  const token = authStorage.getAccessToken()
  if (token) base.searchParams.set('token', token)
  return base.toString()
}

// ─── Provider ──────────────────────────────────────────────────────────────────

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const stateRef = useRef<SocketState>({
    socket: null,
    status: 'idle',
    reconnectTimer: null,
    reconnectAttempts: 0,
    subscriptions: new Map(),
  })

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle')
  const [reconnectAttempt, setReconnectAttempt] = useState(0)

  // ── Dispatch incoming message to matching subscribers ──
  const dispatch = useCallback((envelope: RealtimeEnvelope) => {
    const { subscriptions } = stateRef.current
    for (const [pattern, handlers] of subscriptions) {
      const matches =
        pattern === envelope.topic ||              // exact match
        (pattern.endsWith(':') && envelope.topic.startsWith(pattern)) // prefix wildcard
      if (matches) {
        handlers.forEach((h) => {
          try { h(envelope as RealtimeEnvelope<unknown>) }
          catch (e) { console.warn('[Realtime] handler threw:', e) }
        })
      }
    }
  }, [])

  // ── Connect / Reconnect ──
  const connect = useCallback(() => {
    const state = stateRef.current
    if (state.socket || state.subscriptions.size === 0) return

    state.status = 'connecting'
    setConnectionStatus('connecting')

    let socket: WebSocket
    try {
      socket = new WebSocket(buildWsUrl())
    } catch {
      state.status = 'error'
      setConnectionStatus('error')
      return
    }

    state.socket = socket

    socket.onopen = () => {
      stateRef.current.status = 'open'
      stateRef.current.reconnectAttempts = 0
      setConnectionStatus('open')
      setReconnectAttempt(0)

      // Request a full snapshot on (re)connect so UI is never blank
      try {
        socket.send(JSON.stringify({ op: 'snapshot' }))
      } catch { /* ignore — next reconnect will retry */ }
    }

    socket.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string)
        // Cloud relays raw edge MQTT frames; translate them to dashboard topics
        if (isEdgeFrame(data)) {
          toEnvelopes(data).forEach(dispatch)
          return
        }
        // Support both {topic, type, source, payload} and legacy {type, source, payload}
        const envelope: RealtimeEnvelope = {
          topic: data.topic ?? data.type ?? 'system',
          type: data.event ?? data.type ?? 'message',
          source: data.source ?? '',
          payload: data.payload ?? data,
          ts: data.ts,
        }
        dispatch(envelope)
      } catch {
        // Malformed frame — ignore to keep connection alive
      }
    }

    socket.onerror = () => socket.close()

    socket.onclose = () => {
      const s = stateRef.current
      s.socket = null

      const hasSubscribers = s.subscriptions.size > 0 &&
        [...s.subscriptions.values()].some((set) => set.size > 0)

      s.status = hasSubscribers ? 'closed' : 'idle'
      setConnectionStatus(s.status)

      if (hasSubscribers) {
        const delay = Math.min(500 * 2 ** s.reconnectAttempts, 16_000)
        s.reconnectAttempts += 1
        setReconnectAttempt(s.reconnectAttempts)
        s.reconnectTimer = setTimeout(() => {
          s.reconnectTimer = null
          connect()
        }, delay)
      }
    }
  }, [dispatch])

  // ── Disconnect cleanly on unmount ──
  useEffect(() => {
    return () => {
      const s = stateRef.current
      if (s.reconnectTimer !== null) clearTimeout(s.reconnectTimer)
      s.socket?.close()
    }
  }, [])

  // ── subscribe ──
  const subscribe = useCallback(<T = unknown>(
    topic: string,
    handler: TopicHandler<T>
  ) => {
    const state = stateRef.current
    if (!state.subscriptions.has(topic)) {
      state.subscriptions.set(topic, new Set())
    }
    state.subscriptions.get(topic)!.add(handler as TopicHandler<unknown>)

    // Auto-connect when first subscriber arrives
    connect()

    return () => {
      const handlers = state.subscriptions.get(topic)
      if (handlers) {
        handlers.delete(handler as TopicHandler<unknown>)
        if (handlers.size === 0) state.subscriptions.delete(topic)
      }

      // Disconnect if no subscribers remain
      const hasAny = [...state.subscriptions.values()].some((s) => s.size > 0)
      if (!hasAny) {
        if (state.reconnectTimer !== null) clearTimeout(state.reconnectTimer)
        state.reconnectTimer = null
        state.socket?.close()
        state.socket = null
        state.status = 'idle'
        setConnectionStatus('idle')
      }
    }
  }, [connect])

  // ── publish ──
  const publish = useCallback((topic: RealtimeTopic, type: string, payload?: unknown) => {
    const socket = stateRef.current.socket
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.warn('[Realtime] Cannot publish: socket not open')
      return
    }
    try {
      socket.send(JSON.stringify({ op: 'publish', topic, type, payload }))
    } catch (e) {
      console.warn('[Realtime] publish failed:', e)
    }
  }, [])

  const value = useMemo<RealtimeContextValue>(
    () => ({ subscribe, publish, connectionStatus, reconnectAttempt }),
    [subscribe, publish, connectionStatus, reconnectAttempt]
  )

  return (
    <RealtimeContext.Provider value={value}>
      {children}
    </RealtimeContext.Provider>
  )
}

// ─── Hooks ─────────────────────────────────────────────────────────────────────

function useRealtimeContext(): RealtimeContextValue {
  const ctx = useContext(RealtimeContext)
  if (!ctx) throw new Error('useRealtime* hooks must be used inside <RealtimeProvider>')
  return ctx
}

/**
 * Subscribe to a realtime topic (or prefix wildcard).
 *
 * @example
 * useRealtimeTopic('telemetry:node-hn-01', (msg) => { ... })
 * useRealtimeTopic('alert:', (msg) => { ... })  // all alert topics
 */
export function useRealtimeTopic<T = unknown>(
  topic: string,
  handler: TopicHandler<T>
): ConnectionStatus {
  const { subscribe, connectionStatus } = useRealtimeContext()

  useEffect(() => {
    const unsub = subscribe<T>(topic, handler)
    return unsub
  // handler intentionally omitted — consumers should memoize with useCallback
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topic, subscribe])

  return connectionStatus
}

/**
 * Subscribe to node heartbeat and status events.
 *
 * topic: `node:{nodeId}`
 */
export function useNodeStatus<T = unknown>(nodeId: string, handler: TopicHandler<T>) {
  return useRealtimeTopic<T>(`node:${nodeId}`, handler)
}

/**
 * Subscribe to a specific runtime process stdout/events.
 *
 * topic: `runtime:{nodeId}:{runtimeId}`
 */
export function useRuntimeLogs<T = unknown>(
  nodeId: string,
  runtimeId: string,
  handler: TopicHandler<T>
) {
  return useRealtimeTopic<T>(`runtime:${nodeId}:${runtimeId}`, handler)
}

/**
 * Subscribe to hardware telemetry (CPU, GPU, RAM, temp) for a node.
 *
 * topic: `telemetry:{nodeId}`
 */
export function useTelemetry<T = unknown>(nodeId: string, handler: TopicHandler<T>) {
  return useRealtimeTopic<T>(`telemetry:${nodeId}`, handler)
}

/**
 * Subscribe to safety / PPE / zone detection alerts for a node.
 *
 * topic: `alert:{nodeId}`
 */
export function useAlerts<T = unknown>(nodeId: string | '*', handler: TopicHandler<T>) {
  // Pass wildcard prefix 'alert:' to receive all alert topics
  return useRealtimeTopic<T>(nodeId === '*' ? 'alert:' : `alert:${nodeId}`, handler)
}

/**
 * Subscribe to model deployment progress/status for a node.
 *
 * topic: `deployment:{nodeId}`
 */
export function useDeployment<T = unknown>(nodeId: string | '*', handler: TopicHandler<T>) {
  return useRealtimeTopic<T>(nodeId === '*' ? 'deployment:' : `deployment:${nodeId}`, handler)
}

/**
 * Subscribe to global system events (auth, connectivity, announcements).
 *
 * topic: `system`
 */
export function useSystemEvents<T = unknown>(handler: TopicHandler<T>) {
  return useRealtimeTopic<T>('system', handler)
}

/**
 * Expose publish and connection status to any component.
 */
export function useRealtime() {
  return useRealtimeContext()
}

/**
 * @deprecated Use useRealtimeTopic / useNodeStatus / useTelemetry / useAlerts instead.
 * Kept for backward compatibility.
 */
export function useRealtimeChannel(
  channel: 'telemetry' | 'alerts' | 'logs',
  handler: TopicHandler<unknown>
): ConnectionStatus {
  const topicMap = { telemetry: 'telemetry:', alerts: 'alert:', logs: 'runtime:' }
  return useRealtimeTopic(topicMap[channel], handler)
}
