export type Severity = 'critical' | 'warning' | 'info'
export type IncidentStatus = 'New' | 'Reviewed' | 'Escalated'

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: 'CRITICAL', warning: 'WARNING', info: 'INFO',
}

export const STATUS_LABEL: Record<IncidentStatus, string> = {
  New: 'New', Reviewed: 'Reviewed', Escalated: 'Escalated',
}

export interface Incident {
  id: number
  time: string
  camera: string
  event: string
  confidence: number
  severity: Severity
  status: IncidentStatus
  personId: string
  location: string
  explanation: string
}

export interface AnalyticsPoint {
  time: string
  violations: number
  people: number
  complianceRate: number
}

export interface MonitoringPoint {
  time: string
  cpuAvg: number
  gpuAvg: number
  ramAvg: number
  fpsAvg: number
  latencyP50: number
  latencyP95: number
  networkMbps: number
}

export interface TimelineEvent {
  id: string
  timestamp: string
  source: 'Edge Device' | 'AI Inference' | 'Camera' | 'Deployment' | 'Security'
  severity: 'info' | 'warning' | 'critical' | 'success'
  title: string
  details: string
  targetNode: string
}

export interface LogEntry {
  id: string
  timestamp: string
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  component: string
  node: string
  message: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
  timestamp?: string
}
