/**
 * Translates Cloud WebSocket frames into dashboard envelopes.
 *
 * The Cloud relays raw edge MQTT traffic: `{topic: "edge/{cluster}/{node}/{kind}/...", payload, timestamp}`
 * with snake_case contract payloads. Dashboard subscribers listen on `node:` / `telemetry:` / `runtime:` /
 * `deployment:` with NodeAgent-shaped payloads, so this is the one place the two vocabularies meet.
 */
import type { RealtimeEnvelope } from '@/core/realtime/RealtimeContext'
import { mapRuntime, toLogEntry } from '@/modules/agent/services/logs'
import { gpuMetrics, systemMetrics, toNodeStatus } from '@/modules/cluster/services/cluster'

type Json = Record<string, unknown>

interface EdgeFrame {
  topic: string
  payload: Json
  timestamp?: string
}

export const isEdgeFrame = (data: unknown): data is EdgeFrame =>
  typeof data === 'object' && data !== null && typeof (data as EdgeFrame).topic === 'string'
  && (data as EdgeFrame).topic.startsWith('edge/')

const envelope = (topic: string, type: string, source: string, payload: unknown, ts?: string): RealtimeEnvelope =>
  ({ topic, type, source, payload, ts })

function runtimeEnvelopes(node: string, runtimes: Json[], ts?: string): RealtimeEnvelope[] {
  return runtimes.map((r) => envelope(`runtime:${node}`, 'status', node, mapRuntime({
    id: String(r.runtime_id), node_id: node, name: String(r.name), type: 'vision', status: String(r.status),
    image_uri: (r.image as string | null) ?? null, image_tag: null, model_id: null, config: {},
    container_id: (r.container_id as string | null) ?? null, started_at: (r.started_at as string | null) ?? null,
    stopped_at: null,
  }), ts))
}

/** Zero or more dashboard envelopes for one Cloud frame. */
export function toEnvelopes({ topic, payload, timestamp }: EdgeFrame): RealtimeEnvelope[] {
  // edge/{cluster}/{node}/{kind}/{sub?}
  const [, , node, kind, sub] = topic.split('/')
  if (!node) return []

  if (kind === 'telemetry' && sub === 'system') {
    return [envelope(`telemetry:${node}`, 'metric', node, systemMetrics(payload), timestamp)]
  }
  if (kind === 'telemetry' && sub === 'gpu') {
    return [envelope(`telemetry:${node}`, 'metric', node, gpuMetrics(payload), timestamp)]
  }
  if (kind === 'state' && sub === undefined) {
    return [
      envelope(`node:${node}`, 'status', node, { status: toNodeStatus(payload.agent_status as string), lastHeartbeat: 'just now' }, timestamp),
      ...runtimeEnvelopes(node, (payload.runtimes as Json[] | undefined) ?? [], timestamp),
    ]
  }
  if (kind === 'logs' && sub) {
    const lines = (payload.lines as { timestamp: string; level: string; message: string }[] | undefined) ?? []
    return lines.map((line, i) => envelope(`runtime:${node}`, 'log', node,
      toLogEntry({ node_id: node, runtime_id: sub, ...line }, i), line.timestamp))
  }
  if (kind === 'event' && sub === 'deployment') {
    return [envelope(`deployment:${node}`, 'changed', node, payload, timestamp)]
  }
  return []
}
