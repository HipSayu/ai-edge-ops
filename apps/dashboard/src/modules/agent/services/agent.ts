import type { Snapshot, DetectionEvent, Camera, CameraGroup, EdgeDevice, BackendMetricSample } from '@/modules/agent/types/agent'
import type { BackendNode, BackendRuntime, NodeAgent } from '@/modules/cluster/types/cluster'
import { fetchTelemetry, mapNode } from '@/modules/cluster/services/cluster'
import { apiClient } from '@/shared/api/client'

const toDevice = ({ clusterId: _c, cameras: _cams, ...node }: NodeAgent): EdgeDevice => ({ ...node, assignedCameras: 0 })

const loadDevice = async (node: BackendNode) => {
  const [telemetry, runtimes] = await Promise.all([
    fetchTelemetry(node.id),
    apiClient.get<BackendRuntime[]>('/runtimes', { query: { node_id: node.id } }).catch((): BackendRuntime[] => []),
  ])
  return toDevice(mapNode(node, telemetry, runtimes))
}

const num = (v: unknown) => (typeof v === 'number' ? v : null)

// `telemetry/system` history → the metric sample shape the charts expect.
const toSample = (t: Record<string, unknown>): BackendMetricSample => ({
  recorded_at: String(t.timestamp ?? ''),
  cpu_percent: num(t.cpu_usage_pct),
  gpu_percent: null,
  mem_percent: num(t.memory_usage_pct),
  mem_used_mb: num(t.memory_used_mb),
  mem_total_mb: t.memory_used_mb != null && t.memory_available_mb != null ? Number(t.memory_used_mb) + Number(t.memory_available_mb) : null,
  disk_percent: num(t.disk_usage_pct),
  temperature_c: num(t.temperature_c),
  fps: null,
  inference_latency_ms: null,
})

// Cameras, camera groups, snapshots and detection events have no Cloud API endpoint yet.
export const agentService = {
  createDevice: async (payload: { cluster_id: string; name: string; metadata?: Record<string, unknown> }) =>
    loadDevice(await apiClient.post<BackendNode>('/nodes', payload)),
  listDevices: async () => Promise.all((await apiClient.get<BackendNode[]>('/nodes')).map(loadDevice)),
  getDevice: async (id: string) => loadDevice(await apiClient.get<BackendNode>(`/nodes/${id}`)),
  listDeviceMetrics: async (nodeId: string) =>
    (await apiClient.get<Record<string, unknown>[]>(`/monitoring/nodes/${nodeId}/telemetry/system`, { query: { limit: 300 } }))
      .map(toSample)
      .reverse(),
  listNodeEvents: (nodeId: string, limit = 100) =>
    apiClient.get<Record<string, unknown>[]>(`/monitoring/nodes/${nodeId}/events`, { query: { limit } }),
  // Endpoints below are not implemented by the cloud API yet; callers treat failures as "no data".
  listCameras: () => apiClient.get<Camera[]>('/cameras'),
  getCamera: (id: string) => apiClient.get<Camera>(`/cameras/${id}`),
  createCamera: (payload: { node_id: string; name: string; zone?: string; stream_url?: string; resolution?: string; fps?: number; model?: string }) =>
    apiClient.post<Camera>('/cameras', payload),
  listCameraGroups: () => apiClient.get<CameraGroup[]>('/camera-groups'),
  createCameraGroup: (payload: { name: string; description?: string; site: string; camera_ids: number[] }) =>
    apiClient.post<CameraGroup>('/camera-groups', payload),
  getCameraGroup: (id: string) => apiClient.get<CameraGroup>(`/camera-groups/${id}`),
  listSnapshots: (cameraId?: string) => apiClient.get<Snapshot[]>('/snapshots', { query: { camera_id: cameraId } }),
  listDetectionEvents: () => apiClient.get<DetectionEvent[]>('/detections'),
}
