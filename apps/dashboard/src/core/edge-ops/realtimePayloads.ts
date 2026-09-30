/** Payload shapes of realtime envelopes consumed by EdgeOpsContext. */
import type { NodeAgent } from '@/modules/cluster/types/cluster'

export type NodeStatusPayload = Pick<NodeAgent, 'status' | 'lastHeartbeat'> & Partial<Pick<NodeAgent, 'uptime'>>

export type TelemetryPayload = Pick<NodeAgent, 'cpuUsage' | 'gpuUsage' | 'ramUsedGb' | 'diskUsage' | 'tempC'>

export interface CameraStatusPayload {
  nodeId: string
  online: boolean
  fps: number
}

export interface ClassStatsPayload {
  detectionCount24h: number
  lastSeen: string
}
