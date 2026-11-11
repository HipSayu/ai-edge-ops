import { api } from '@/api/client'
import type { GridItem, Stats } from '@/api/types'

export const gridService = {
  grid: (clusterId: number | null) => api.get<GridItem[]>('/grid', { cluster_id: clusterId }),
  stats: (clusterId: number | null, sinceMinutes = 60) =>
    api.get<Stats>('/stats', { cluster_id: clusterId, since_minutes: sinceMinutes }),
}
