import type { Incident } from '@/modules/observability/mock/incidents'
import type { MonitoringPoint } from '@/modules/observability/mock/observability'
import { apiClient } from './client'

export const observabilityService = {
  listIncidents: (query?: { status?: string; severity?: string }) =>
    apiClient.get<Incident[]>('/observability/incidents', { query }),
  getIncident: (incidentId: number | string) =>
    apiClient.get<Incident>(`/observability/incidents/${incidentId}`),
  updateIncident: (incidentId: number | string, payload: Partial<Incident>) =>
    apiClient.patch<Incident>(`/observability/incidents/${incidentId}`, payload),
  listEvents: () => apiClient.get<unknown[]>('/observability/events'),
  listLogs: (query?: { level?: string; node?: string }) =>
    apiClient.get<unknown[]>('/observability/logs', { query }),
  getMonitoringTimeline: () => apiClient.get<MonitoringPoint[]>('/observability/monitoring'),
}
