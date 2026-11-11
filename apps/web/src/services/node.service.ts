import { api } from '@/api/client'
import type { NodeItem } from '@/api/types'

export type NodeInput = Pick<NodeItem, 'cluster_id' | 'name' | 'description' | 'ip_address'>

export const nodeService = {
  list: (clusterId?: number | null) =>
    api.get<NodeItem[]>('/nodes', clusterId ? { cluster_id: clusterId } : undefined),
  create: (input: NodeInput) => api.post<NodeItem>('/nodes', input),
  update: (id: number, input: NodeInput) => api.put<NodeItem>(`/nodes/${id}`, input),
  remove: (id: number) => api.del<void>(`/nodes/${id}`),
}

