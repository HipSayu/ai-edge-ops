export type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'DEBUG' | 'TRACE'

export type RuntimeId =
  | 'agent-core'
  | 'vision-runtime'
  | 'rtsp-streamer'
  | 'inference-worker'
  | 'webrtc-gateway'
  | 'systemd-health'

export interface RuntimeProcess {
  id: RuntimeId
  name: string
  description: string
  status: 'running' | 'degraded' | 'stopped' | 'failed'
  pid: number
  cpuPercent: number
  memoryMb: number
  uptime: string
  version: string
  errorCount24h: number
}

export interface NodeLogEntry {
  id: string
  timestamp: string
  level: LogLevel
  runtime: RuntimeId
  nodeId: string
  clusterId: string
  message: string
  details?: Record<string, unknown>
}

export interface NodeLogFilter {
  clusterId?: string
  nodeId?: string
  runtime?: RuntimeId | 'all'
  level?: LogLevel | 'ALL'
  search?: string
  limit?: number
}
