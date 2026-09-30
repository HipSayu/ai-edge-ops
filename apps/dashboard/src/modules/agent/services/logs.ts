import type { LogLevel, RuntimeId, RuntimeProcess, NodeLogEntry, NodeLogFilter } from '@/modules/agent/types/logs'
import type { BackendRuntime } from '@/modules/cluster/types/cluster'
import { apiClient } from '@/shared/api/client'

const runtimeStatus: Record<string, RuntimeProcess['status']> = {
  RUNNING: 'running', DEGRADED: 'degraded', STOPPED: 'stopped', FAILED: 'failed',
}

const formatUptime = (startedAt: string | null) => {
  if (!startedAt) return '—'
  const min = Math.max(0, Math.floor((Date.now() - new Date(startedAt).getTime()) / 60_000))
  return min >= 60 ? `${Math.floor(min / 60)}h ${min % 60}m` : `${min}m`
}

export const mapRuntime = (r: BackendRuntime): RuntimeProcess => ({
  id: r.id as RuntimeId,
  name: r.name,
  description: r.model_id ?? r.image_uri ?? r.type,
  status: runtimeStatus[r.status.toUpperCase()] ?? 'stopped',
  pid: 0,
  cpuPercent: 0,
  memoryMb: 0,
  uptime: formatUptime(r.started_at),
  version: r.image_tag ?? '—',
  errorCount24h: 0,
})

/** One line from GET /runtimes/{id}/logs or an `edge/.../logs/{runtime_id}` realtime batch. */
export interface BackendLogLine {
  node_id: string
  runtime_id: string
  timestamp: string
  level: string
  message: string
}

const logLevel: Record<string, LogLevel> = {
  DEBUG: 'DEBUG', INFO: 'INFO', WARNING: 'WARN', ERROR: 'ERROR', CRITICAL: 'ERROR',
}

export const toLogEntry = (line: BackendLogLine, index = 0): NodeLogEntry => ({
  id: `${line.runtime_id}:${line.timestamp}:${index}`,
  timestamp: line.timestamp,
  level: logLevel[line.level] ?? 'INFO',
  runtime: line.runtime_id as RuntimeId,
  nodeId: line.node_id,
  clusterId: '',
  message: line.message,
})

export const logsService = {
  listRuntimes: async (nodeId?: string): Promise<(RuntimeProcess & { nodeId: string })[]> =>
    (await apiClient.get<BackendRuntime[]>('/runtimes', { query: { node_id: nodeId } }))
      .map((r) => ({ ...mapRuntime(r), nodeId: r.node_id })),
  controlRuntime: (runtimeId: string, action: 'start' | 'stop' | 'restart' | 'update' | 'remove') =>
    apiClient.post<unknown>(`/runtimes/${encodeURIComponent(runtimeId)}/${action}`),
  /** Recent logs of every runtime on a node, oldest first (new lines then stream in via RealtimeContext). */
  listNodeLogs: async ({ nodeId, limit = 200 }: NodeLogFilter = {}): Promise<NodeLogEntry[]> => {
    if (!nodeId) return []
    const runtimes = await apiClient.get<BackendRuntime[]>('/runtimes', { query: { node_id: nodeId } })
    const perRuntime = await Promise.all(runtimes.map((r) =>
      apiClient.get<BackendLogLine[]>(`/runtimes/${encodeURIComponent(r.id)}/logs`, { query: { limit } })
        .catch((): BackendLogLine[] => [])))
    return perRuntime.flat()
      .sort((a, b) => a.timestamp.localeCompare(b.timestamp))
      .map(toLogEntry)
  },
}
