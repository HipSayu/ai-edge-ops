import type {
  BackendCluster, BackendHealth, BackendNode, BackendRuntime, BackendTelemetry, Cluster, ClusterStatus, NodeAgent,
} from '@/modules/cluster/types/cluster'
import { apiClient } from '@/shared/api/client'

const round = (n: number, d = 0) => Math.round(n * 10 ** d) / 10 ** d
const num = (v: unknown) => (typeof v === 'number' && Number.isFinite(v) ? v : 0)

const formatUptime = (seconds: number): string => {
  if (seconds <= 0) return 'Unknown'
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return `${d}d ${h}h`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

const clusterStatus: Record<BackendHealth, ClusterStatus> = {
  ONLINE: 'healthy', DEGRADED: 'degraded', OFFLINE: 'offline', UNKNOWN: 'offline',
}
const nodeStatus: Record<BackendHealth, NodeAgent['status']> = {
  ONLINE: 'online', DEGRADED: 'degraded', OFFLINE: 'offline', UNKNOWN: 'offline',
}

export const toNodeStatus = (status: string | undefined): NodeAgent['status'] =>
  nodeStatus[(status ?? 'UNKNOWN').toUpperCase() as BackendHealth] ?? 'offline'

type NodeMetrics = Pick<NodeAgent, 'uptime' | 'cpuUsage' | 'ramUsedGb' | 'diskUsage' | 'tempC'>

/** Node fields from one `telemetry/system` sample (REST latest or realtime). */
export const systemMetrics = (sys: Record<string, unknown>): NodeMetrics => ({
  uptime: formatUptime(num(sys.node_uptime_sec)),
  cpuUsage: round(num(sys.cpu_usage_pct)),
  ramUsedGb: round(num(sys.memory_used_mb) / 1024, 1),
  diskUsage: round(num(sys.disk_usage_pct)),
  tempC: round(num(sys.temperature_c ?? sys.cpu_temperature_c)),
})

/** Node fields from one `telemetry/gpu` sample. */
export const gpuMetrics = (gpu: Record<string, unknown>): Pick<NodeAgent, 'gpuUsage'> => ({
  gpuUsage: round(num(gpu.gpu_usage_pct)),
})

export const mapNode = (node: BackendNode, telemetry: BackendTelemetry = {}, runtimes: BackendRuntime[] = []): NodeAgent => {
  const sys = telemetry.system ?? {}
  const gpu = telemetry.gpu ?? {}
  const memTotalMb = node.memory_total_mb ?? num(sys.memory_used_mb) + num(sys.memory_available_mb)
  const running = runtimes.find((r) => r.status === 'RUNNING') ?? runtimes[0]
  const metrics = systemMetrics(sys)
  return {
    id: node.id,
    name: node.name,
    clusterId: node.cluster_id,
    status: toNodeStatus(node.status),
    ip: node.ip_address ?? 'Not assigned',
    hardware: node.gpu_name ?? (node.cpu_cores ? `${node.cpu_cores} vCPU` : 'edge'),
    agentVersion: node.agent_version ?? 'Unknown',
    ...metrics,
    ...gpuMetrics(gpu),
    tempC: metrics.tempC || round(num(gpu.gpu_temperature_c)),
    ramTotalGb: round(memTotalMb / 1024, 1),
    lastHeartbeat: node.last_heartbeat_at ? new Date(node.last_heartbeat_at).toLocaleString() : 'Never',
    cameras: [],
    modelRunning: running ? (running.model_id ?? `${running.image_uri?.split('/').pop() ?? running.name}:${running.image_tag ?? ''}`) : 'No model reported',
  }
}

/** Latest telemetry for a node; a missing/failing endpoint degrades to "no telemetry". */
export const fetchTelemetry = (nodeId: string) =>
  apiClient.get<BackendTelemetry>(`/monitoring/nodes/${nodeId}/telemetry`).catch((): BackendTelemetry => ({}))

const mapCluster = (cluster: BackendCluster, nodes: NodeAgent[]): Cluster => ({
  id: cluster.id,
  name: cluster.name,
  site: cluster.location ?? '—',
  description: cluster.description ?? '',
  status: clusterStatus[cluster.status] ?? 'offline',
  totalNodes: nodes.length,
  onlineNodes: nodes.filter((n) => n.status === 'online').length,
  totalCameras: 0,
  onlineCameras: 0,
  totalAlerts: 0,
  avgCpuUsage: 0,
  avgGpuUsage: 0,
  avgTempC: 0,
  aggregateFps: 0,
  nodes,
  createdAt: cluster.created_at ?? '',
  updatedAt: cluster.updated_at ?? '',
})

export const clusterService = {
  listClusters: async (): Promise<Cluster[]> => {
    const [clusters, nodes, runtimes] = await Promise.all([
      apiClient.get<BackendCluster[]>('/clusters'),
      apiClient.get<BackendNode[]>('/nodes'),
      apiClient.get<BackendRuntime[]>('/runtimes').catch((): BackendRuntime[] => []),
    ])
    const agents = await Promise.all(
      nodes.map(async (n) => mapNode(n, await fetchTelemetry(n.id), runtimes.filter((r) => r.node_id === n.id))),
    )
    return clusters.map((c) => mapCluster(c, agents.filter((a) => a.clusterId === c.id)))
  },
  createCluster: (payload: { name: string; description?: string; location?: string }) =>
    apiClient.post<BackendCluster>('/clusters', payload),
  registerNode: (payload: { cluster_id: string; name: string; metadata?: Record<string, unknown> }) =>
    apiClient.post<BackendNode>('/nodes', payload),
}
