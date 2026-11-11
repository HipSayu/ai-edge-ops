import { api } from '@/api/client'
import type { Cluster } from '@/api/types'

export type ClusterInput = Pick<Cluster, 'name' | 'description'>

export const clusterService = {
  list: () => api.get<Cluster[]>('/clusters'),
  create: (input: ClusterInput) => api.post<Cluster>('/clusters', input),
  update: (id: number, input: ClusterInput) => api.put<Cluster>(`/clusters/${id}`, input),
  remove: (id: number) => api.del<void>(`/clusters/${id}`),
}

// Backward compatibility alias for any existing imports
export const areaService = {
  list: clusterService.list,
  create: clusterService.create,
  update: clusterService.update,
  remove: clusterService.remove,
}

