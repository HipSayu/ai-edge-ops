export type ClusterStatus = 'healthy' | 'degraded' | 'critical' | 'offline'

export interface CameraOnNode {
  id: string
  name: string
  zone: string
  online: boolean
  fps: number
  resolution: string
  alertCount: number
  model?: string
  streamUrl?: string
}

export interface NodeAgent {
  id: string
  name: string
  clusterId: string
  status: 'online' | 'degraded' | 'offline'
  ip: string
  hardware: string
  agentVersion: string
  uptime: string
  cpuUsage: number
  gpuUsage: number
  ramUsedGb: number
  ramTotalGb: number
  diskUsage: number
  tempC: number
  lastHeartbeat: string
  cameras: CameraOnNode[]
  modelRunning: string
}

export interface Cluster {
  id: string
  name: string
  site: string
  description: string
  status: ClusterStatus
  totalNodes: number
  onlineNodes: number
  totalCameras: number
  onlineCameras: number
  totalAlerts: number
  avgCpuUsage: number
  avgGpuUsage: number
  avgTempC: number
  aggregateFps: number
  nodes: NodeAgent[]
  createdAt: string
  updatedAt: string
}

export interface ClusterSummary {
  totalClusters: number
  healthyClusters: number
  degradedClusters: number
  criticalClusters: number
  offlineClusters: number
  totalNodes: number
  onlineNodes: number
  totalCameras: number
  onlineCameras: number
  totalAlerts: number
}

// ─── Cloud API v1 payloads (apps/cloud/https/router/v1/schemas.py) ─────────────

export type BackendHealth = 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'UNKNOWN'

export interface BackendCluster {
  id: string
  name: string
  description: string | null
  status: BackendHealth
  location: string | null
  metadata: Record<string, unknown>
  created_at: string | null
  updated_at: string | null
}

export interface BackendNode {
  id: string
  cluster_id: string
  name: string
  hostname: string | null
  ip_address: string | null
  status: BackendHealth
  agent_version: string | null
  cpu_cores: number | null
  memory_total_mb: number | null
  gpu_name: string | null
  metadata: Record<string, unknown>
  last_heartbeat_at: string | null
  created_at: string | null
}

export interface BackendRuntime {
  id: string
  node_id: string
  name: string
  type: string
  status: string
  image_uri: string | null
  image_tag: string | null
  model_id: string | null
  config: Record<string, unknown>
  container_id: string | null
  started_at: string | null
  stopped_at: string | null
}

/** GET /monitoring/nodes/{id}/telemetry — latest payload per kind (system, gpu, runtime, ...). */
export type BackendTelemetry = Record<string, Record<string, unknown>>
