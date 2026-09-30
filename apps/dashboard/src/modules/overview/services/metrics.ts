import type { FleetMetricPoint } from '@/modules/ai/types/ai'
import { apiClient } from '@/shared/api/client'

export const metricsService = {
  listFleetMetrics: () => apiClient.get<FleetMetricPoint[]>('/monitoring/fleet/metrics'),
}
