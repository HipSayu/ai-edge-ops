import { apiClient } from '../client'
import type { AlertRecord, AnalyticsOverview, Incident, ViolationLabelCount, ViolationTimeBucket } from '../types/observability'
import type { LogEntry, MonitoringPoint, TimelineEvent } from '@/modules/observability/types'

const mapAlert = (alert: AlertRecord): Incident => ({
  id: alert.id, time: new Date(alert.created_at).toLocaleTimeString(), camera: alert.device_id === null ? 'Agent' : `Device ${alert.device_id}`,
  event: alert.title, confidence: 1, severity: alert.severity,
  status: alert.status === 'open' ? 'New' : alert.status === 'acknowledged' ? 'Reviewed' : 'Escalated',
  personId: '-', location: alert.device_id === null ? 'Platform' : `Edge device ${alert.device_id}`,
  explanation: alert.description ?? alert.type,
})

const ALERT_TYPE_SOURCE: Record<string, TimelineEvent['source']> = {
  device_offline: 'Edge Device',
  latency_degraded: 'AI Inference',
  ppe_violation: 'Security',
  deployment_failed: 'Deployment',
}

const mapAlertToEvent = (alert: AlertRecord): TimelineEvent => ({
  id: String(alert.id),
  timestamp: new Date(alert.created_at).toLocaleString(),
  source: ALERT_TYPE_SOURCE[alert.type] ?? 'Edge Device',
  severity: alert.severity,
  title: alert.title,
  details: alert.description ?? alert.type,
  targetNode: alert.device_id === null ? 'Platform' : `Device ${alert.device_id}`,
})

export const observabilityService = {
  listIncidents: async (query?: { status?: string; severity?: string }) => (await apiClient.get<{ items: AlertRecord[] }>('/alerts', { query })).items.map(mapAlert),
  getIncident: (id: number | string) => apiClient.get<Incident>(`/alerts/${id}`),
  acknowledgeIncident: (id: number | string) => apiClient.post<Incident>(`/alerts/${id}/acknowledge`),
  resolveIncident: (id: number | string) => apiClient.post<Incident>(`/alerts/${id}/resolve`),
  listEvents: async () => (await apiClient.get<{ items: AlertRecord[] }>('/alerts')).items.map(mapAlertToEvent),
  // No backend log-streaming endpoint exists yet; return an empty buffer rather than
  // force-fitting the unrelated violations-timeseries shape into LogEntry (crashes on undefined fields).
  listLogs: async (_query?: { level?: string; node?: string }): Promise<LogEntry[]> => [],
  // Same: no backend endpoint yet exposes a GPU/CPU/latency time series.
  getMonitoringTimeline: async (): Promise<MonitoringPoint[]> => [],
  getAnalyticsOverview: () => apiClient.get<AnalyticsOverview>('/analytics/overview'),
  getViolationTimeseries: (days = 14) => apiClient.get<ViolationTimeBucket[]>('/analytics/violations/timeseries', { query: { days } }),
  getViolationsByType: (days = 30) => apiClient.get<ViolationLabelCount[]>('/analytics/violations/by-type', { query: { days } }),
}
