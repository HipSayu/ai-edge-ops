export type Severity = 'critical' | 'warning' | 'info'
export type IncidentStatus = 'New' | 'Reviewed' | 'Escalated'
export const SEVERITY_LABEL: Record<Severity, string> = { critical: 'CRITICAL', warning: 'WARNING', info: 'INFO' }
export const STATUS_LABEL: Record<IncidentStatus, string> = { New: 'New', Reviewed: 'Reviewed', Escalated: 'Escalated' }
export interface Incident { id: number; time: string; camera: string; event: string; confidence: number; severity: Severity; status: IncidentStatus; personId: string; location: string; explanation: string }
export interface AnalyticsPoint { time: string; violations: number; people: number; complianceRate: number }
export interface MonitoringPoint { time: string; cpuAvg: number; gpuAvg: number; ramAvg: number; fpsAvg: number; latencyP50: number; latencyP95: number; networkMbps: number }
export interface ChatMessage { id: number; role: 'user' | 'assistant'; text: string; timestamp?: string }
export type AlertRecord = { id: number; type: string; severity: Severity; status: 'open' | 'acknowledged' | 'resolved'; title: string; description: string | null; device_id: number | null; created_at: string }
export type AnalyticsOverview = { devices_total: number; devices_online: number; active_deployments: number; open_alerts: number; violations_24h: number; avg_inference_latency_ms: number | null }
export type ViolationTimeBucket = { bucket: string; count: number }
export type ViolationLabelCount = { label: string; count: number }
export type MonitoringTimeline = MonitoringPoint
export type ObservabilityIncident = Incident
