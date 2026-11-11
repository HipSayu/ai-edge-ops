import { api } from '@/api/client'
import type { Camera, ViolationEvent, Zone } from '@/api/types'

// A camera cannot change node: its video folder is named after the node
export type CameraInput = Pick<Camera, 'name' | 'enabled'> & { zone?: string | null }

export interface SyncResult {
  cameras: number
  videos: number
  unmatched_folders: string[]
}

export const cameraService = {
  list: (nodeId?: number | null) =>
    api.get<Camera[]>('/cameras', nodeId ? { node_id: nodeId } : undefined),
  update: (id: number, input: CameraInput) => api.put<Camera>(`/cameras/${id}`, input),
  remove: (id: number) => api.del<void>(`/cameras/${id}`),
  // Creates a camera on the node and stores its first video
  upload: (file: File, name: string, nodeId: number | null, clusterId: number | null) => {
    const form = new FormData()
    form.append('file', file)
    form.append('name', name)
    if (nodeId !== null) form.append('node_id', String(nodeId))
    if (clusterId !== null) form.append('cluster_id', String(clusterId))
    return api.upload<Camera>('/cameras/upload', form)
  },
  sync: () => api.post<SyncResult>('/cameras/sync'),
  // The forbidden zones of a camera; saving replaces them all and sends them to the edge that runs the camera
  zones: (id: number) => api.get<Zone[]>(`/cameras/${id}/zones`),
  saveZones: (id: number, zones: Zone[]) => api.put<Zone[]>(`/cameras/${id}/zones`, { zones }),
  events: (id: number, limit = 30) => api.get<ViolationEvent[]>(`/cameras/${id}/events`, { limit }),
}
